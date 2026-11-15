using System;
using System.Collections.Generic;

namespace InvoiceImport;

public static class InvoiceValidator
{
    public static IReadOnlyList<RowIssue> Validate(NormalizedInvoice invoice, DateOnly today)
    {
        var issues = new List<RowIssue>();
        ValidateIdentifier(invoice.Line, "supplier", invoice.Supplier, 120, issues);
        ValidateIdentifier(invoice.Line, "number", invoice.Number, 64, issues);

        if (invoice.Date < new DateOnly(2000, 1, 1))
        {
            issues.Add(new RowIssue(invoice.Line, "date", "too-old", "Invoice dates must be in the supported accounting period."));
        }

        if (invoice.Date > today)
        {
            issues.Add(new RowIssue(invoice.Line, "date", "future", "Invoice dates cannot be in the future."));
        }

        if (invoice.Currency != "EUR" && invoice.Currency != "USD" && invoice.Currency != "GBP")
        {
            issues.Add(new RowIssue(invoice.Line, "currency", "unsupported", "Currency must be EUR, USD, or GBP."));
        }

        if (invoice.Net < 0m || invoice.Net > 1000000m)
        {
            issues.Add(new RowIssue(invoice.Line, "net", "range", "Net amount must be between zero and one million."));
        }

        if (invoice.Tax.HasValue)
        {
            issues.AddRange(ValidateTax(invoice.Line, invoice.Net, invoice.Tax.Value));
        }

        return issues.AsReadOnly();
    }

    public static IReadOnlyList<RowIssue> ValidateTax(int line, decimal net, decimal tax)
    {
        var issues = new List<RowIssue>();
        if (tax < 0m)
        {
            issues.Add(new RowIssue(line, "tax", "negative", "Tax cannot be negative."));
        }

        if (tax > net)
        {
            issues.Add(new RowIssue(line, "tax", "range", "Tax cannot exceed the net amount."));
        }

        if (decimal.Round(tax, 2) != tax)
        {
            issues.Add(new RowIssue(line, "tax", "precision", "Resolved tax must have at most two decimal places."));
        }

        return issues.AsReadOnly();
    }

    private static void ValidateIdentifier(int line, string field, string value, int maximum, List<RowIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new RowIssue(line, field, "required", "The identifier is required."));
            return;
        }

        if (value.Length > maximum)
        {
            issues.Add(new RowIssue(line, field, "length", "The identifier exceeds its length limit."));
        }

        foreach (char character in value)
        {
            if (char.IsControl(character))
            {
                issues.Add(new RowIssue(line, field, "control-character", "Control characters are not allowed."));
                break;
            }
        }
    }
}