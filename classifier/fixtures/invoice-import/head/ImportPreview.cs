using System;
using System.Collections.Generic;
using System.Linq;

namespace InvoiceImport;

public sealed class ImportPreview
{
    private readonly DuplicatePolicy duplicates;

    public ImportPreview(IInvoiceStore store)
    {
        duplicates = new DuplicatePolicy(store);
    }

    public ImportPreviewResult Create(string tenant, string csv, DateOnly today)
    {
        BatchImporter.RequireTenant(tenant);
        CsvDocument document = CsvInvoiceReader.Read(csv, 10000);
        var rows = new List<PreviewRow>();
        if (!document.HeaderValid || document.Issues.Any(issue => issue.Field == "file"))
        {
            return new ImportPreviewResult(tenant, rows, document.Issues, 0, 0);
        }

        ISet<string> seen = DuplicatePolicy.NewBatch();
        foreach (RawInvoiceRow raw in document.Rows)
        {
            NormalizationResult result = InvoiceNormalizer.Normalize(raw);
            if (result.Value == null)
            {
                rows.Add(new PreviewRow(raw.Line, raw.Supplier, raw.Number, raw.Currency, 0m, null, false, result.Issues));
                continue;
            }

            NormalizedInvoice invoice = result.Value;
            var issues = new List<RowIssue>(InvoiceValidator.Validate(invoice, today));
            if (issues.Count == 0)
            {
                RowIssue duplicate = duplicates.Check(tenant, invoice, seen);
                if (duplicate != null)
                {
                    issues.Add(duplicate);
                }
            }

            if (!invoice.Tax.HasValue)
            {
                issues.Add(new RowIssue(invoice.Line, "tax", "provider-needed", "Tax needs a provider contract before import."));
            }

            bool ready = issues.Count == 0;
            if (ready)
            {
                duplicates.Remember(tenant, invoice, seen);
            }

            rows.Add(new PreviewRow(
                invoice.Line,
                invoice.Supplier,
                invoice.Number,
                invoice.Currency,
                invoice.Net,
                invoice.Tax,
                ready,
                issues.AsReadOnly()));
        }

        foreach (var group in document.Issues.GroupBy(issue => issue.Line))
        {
            rows.Add(new PreviewRow(group.Key, string.Empty, string.Empty, string.Empty, 0m, null, false, group.ToArray()));
        }

        PreviewRow[] ordered = rows.OrderBy(row => row.Line).ToArray();
        return new ImportPreviewResult(
            tenant,
            Array.AsReadOnly(ordered),
            Array.Empty<RowIssue>(),
            ordered.Count(row => row.CanImport),
            ordered.Count(row => !row.CanImport));
    }
}