using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace InvoiceImport;

public sealed class BatchImporter
{
    private readonly DuplicatePolicy duplicatePolicy;
    private readonly RetryingInvoiceWriter writer;

    public BatchImporter(IInvoiceStore store, int maximumAttempts = 3)
    {
        duplicatePolicy = new DuplicatePolicy(store);
        writer = new RetryingInvoiceWriter(store, maximumAttempts);
    }

    public BatchReport Import(string tenant, string csv, DateOnly today, object taxProvider, CancellationToken cancellation)
    {
        RequireTenant(tenant);
        cancellation.ThrowIfCancellationRequested();
        CsvDocument document = CsvInvoiceReader.Read(csv, 10000);
        RowIssue[] fileIssues = document.Issues.Where(issue => issue.Field == "file" || !document.HeaderValid).ToArray();
        if (!document.HeaderValid || fileIssues.Length > 0)
        {
            return BatchReconciler.Build(tenant, Array.Empty<RowOutcome>(), fileIssues);
        }

        var outcomes = new List<RowOutcome>();
        foreach (var group in document.Issues.GroupBy(issue => issue.Line))
        {
            outcomes.Add(BatchReconciler.Reject(group.Key, group));
        }

        ISet<string> seen = DuplicatePolicy.NewBatch();
        foreach (RawInvoiceRow source in document.Rows)
        {
            cancellation.ThrowIfCancellationRequested();
            NormalizationResult normalized = InvoiceNormalizer.Normalize(source);
            if (normalized.Value == null)
            {
                outcomes.Add(BatchReconciler.Reject(source.Line, normalized.Issues));
                continue;
            }

            NormalizedInvoice invoice = normalized.Value;
            IReadOnlyList<RowIssue> validation = InvoiceValidator.Validate(invoice, today);
            if (validation.Count > 0)
            {
                outcomes.Add(BatchReconciler.Reject(source.Line, validation));
                continue;
            }

            RowIssue duplicate = duplicatePolicy.Check(tenant, invoice, seen);
            if (duplicate != null)
            {
                outcomes.Add(BatchReconciler.Reject(source.Line, new[] { duplicate }));
                continue;
            }

            decimal tax;
            try
            {
                tax = TaxGateway.Resolve(invoice, taxProvider);
            }
            catch (Exception error) when (error is InvalidOperationException || error is Microsoft.CSharp.RuntimeBinder.RuntimeBinderException)
            {
                var issue = new RowIssue(source.Line, "tax", "provider-unavailable", "Tax could not be resolved for this row.");
                outcomes.Add(BatchReconciler.Reject(source.Line, new[] { issue }));
                continue;
            }

            WriteResult result = writer.Write(tenant, invoice, tax);
            if (!result.Succeeded)
            {
                var issue = new RowIssue(source.Line, "store", "write-failed", result.Error);
                outcomes.Add(BatchReconciler.Reject(source.Line, new[] { issue }));
                continue;
            }

            duplicatePolicy.Remember(tenant, invoice, seen);
            outcomes.Add(BatchReconciler.Accept(invoice, tax, result.Id.Value));
        }

        return BatchReconciler.Build(tenant, outcomes, Array.Empty<RowIssue>());
    }

    public static void RequireTenant(string tenant)
    {
        if (string.IsNullOrWhiteSpace(tenant) || tenant.Length > 100 || tenant.Any(char.IsControl))
        {
            throw new ArgumentException("A valid tenant identity is required.");
        }
    }
}