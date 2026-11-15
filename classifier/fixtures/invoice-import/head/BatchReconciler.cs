using System;
using System.Collections.Generic;
using System.Linq;

namespace InvoiceImport;

public static class BatchReconciler
{
    public static BatchReport Build(string tenant, IEnumerable<RowOutcome> source, IEnumerable<RowIssue> fileIssues)
    {
        RowOutcome[] rows = source.OrderBy(row => row.Line).ToArray();
        RowIssue[] failures = fileIssues.ToArray();
        if (rows.Select(row => row.Line).Distinct().Count() != rows.Length)
        {
            throw new ArgumentException("A source row may have only one outcome.");
        }

        foreach (var row in rows)
        {
            ValidateOutcome(row);
        }

        RowOutcome[] accepted = rows.Where(row => row.State == "accepted").ToArray();
        int rejected = rows.Length - accepted.Length;
        var totals = new List<CurrencyTotal>();
        foreach (var group in accepted.GroupBy(row => row.Currency).OrderBy(group => group.Key, StringComparer.Ordinal))
        {
            decimal net = group.Sum(row => row.Net);
            decimal tax = group.Sum(row => row.Tax);
            totals.Add(new CurrencyTotal(group.Key, net, tax, checked(net + tax)));
        }

        string state;
        if (failures.Length > 0)
        {
            state = "file-rejected";
        }
        else if (rejected > 0)
        {
            state = accepted.Length > 0 ? "partial-success" : "rejected";
        }
        else
        {
            state = "completed";
        }

        return new BatchReport(
            tenant,
            state,
            rows.Length,
            accepted.Length,
            rejected,
            Array.AsReadOnly(rows),
            totals.AsReadOnly(),
            Array.AsReadOnly(failures));
    }

    public static RowOutcome Reject(int line, IEnumerable<RowIssue> issues)
    {
        var failures = issues.ToArray();
        if (failures.Length == 0)
        {
            throw new ArgumentException("Rejected rows require a reason.");
        }

        return new RowOutcome(line, "rejected", null, string.Empty, 0m, 0m, Array.AsReadOnly(failures));
    }

    public static RowOutcome Accept(NormalizedInvoice row, decimal tax, Guid id)
    {
        return new RowOutcome(row.Line, "accepted", id, row.Currency, row.Net, tax, Array.Empty<RowIssue>());
    }

    private static void ValidateOutcome(RowOutcome row)
    {
        if (row.Line < 1 || (row.State != "accepted" && row.State != "rejected"))
        {
            throw new ArgumentException("Invalid row outcome.");
        }

        if (row.State == "accepted" && (!row.InvoiceId.HasValue || row.Issues.Count > 0 || row.Net < 0m || row.Tax < 0m))
        {
            throw new ArgumentException("Accepted rows require an invoice identity and valid amounts.");
        }

        if (row.State == "rejected" && (row.InvoiceId.HasValue || row.Issues.Count == 0 || row.Net != 0m || row.Tax != 0m))
        {
            throw new ArgumentException("Rejected rows cannot contribute invoice amounts.");
        }
    }
}