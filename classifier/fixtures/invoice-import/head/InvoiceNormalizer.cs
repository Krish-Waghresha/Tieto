using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace InvoiceImport;

public static class InvoiceNormalizer
{
    public static NormalizationResult Normalize(RawInvoiceRow row)
    {
        var issues = new List<RowIssue>();
        string supplier = NormalizeKey(row.Supplier);
        string number = NormalizeKey(row.Number);
        string currency = (row.Currency ?? string.Empty).Trim().ToUpperInvariant();
        DateOnly date;
        if (!DateOnly.TryParseExact(row.Date.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out date))
        {
            issues.Add(new RowIssue(row.Line, "date", "format", "Use an ISO date in yyyy-MM-dd format."));
        }

        decimal net;
        if (!TryMoney(row.Net, out net))
        {
            issues.Add(new RowIssue(row.Line, "net", "format", "Use an invariant decimal amount."));
        }
        else if (net < 0m)
        {
            issues.Add(new RowIssue(row.Line, "net", "negative", "Net amount cannot be negative before rounding."));
        }

        decimal? tax = null;
        if (!string.IsNullOrWhiteSpace(row.Tax))
        {
            decimal parsedTax;
            if (TryMoney(row.Tax, out parsedTax))
            {
                if (parsedTax < 0m)
                {
                    issues.Add(new RowIssue(row.Line, "tax", "negative", "Tax cannot be negative before rounding."));
                }
                else
                {
                    tax = RoundMoney(parsedTax);
                }
            }
            else
            {
                issues.Add(new RowIssue(row.Line, "tax", "format", "Use an invariant decimal amount."));
            }
        }

        if (issues.Count > 0)
        {
            return new NormalizationResult(null, issues.AsReadOnly());
        }

        return new NormalizationResult(
            new NormalizedInvoice(row.Line, supplier, number, date, currency, RoundMoney(net), tax),
            issues.AsReadOnly());
    }

    public static string NormalizeKey(string value)
    {
        if (value == null)
        {
            return string.Empty;
        }

        return value.Trim().Normalize(NormalizationForm.FormC).ToUpperInvariant();
    }

    public static decimal RoundMoney(decimal value)
    {
        return decimal.Round(value, 2, MidpointRounding.AwayFromZero);
    }

    public static bool TryMoney(string text, out decimal value)
    {
        value = 0m;
        if (string.IsNullOrWhiteSpace(text))
        {
            return false;
        }

        string trimmed = text.Trim();
        int fractionalDigits = 0;
        bool decimalSeen = false;
        for (int index = 0; index < trimmed.Length; index++)
        {
            char character = trimmed[index];
            if (index == 0 && (character == '-' || character == '+'))
            {
                continue;
            }

            if (character == '.' && !decimalSeen)
            {
                decimalSeen = true;
                continue;
            }

            if (character < '0' || character > '9')
            {
                return false;
            }

            if (decimalSeen)
            {
                fractionalDigits++;
            }
        }

        if (fractionalDigits > 4)
        {
            return false;
        }

        return decimal.TryParse(trimmed,
            NumberStyles.AllowLeadingSign | NumberStyles.AllowDecimalPoint,
            CultureInfo.InvariantCulture,
            out value);
    }

    public static IReadOnlyList<NormalizationResult> NormalizeAll(IEnumerable<RawInvoiceRow> rows)
    {
        var normalized = new List<NormalizationResult>();
        foreach (var row in rows)
        {
            normalized.Add(Normalize(row));
        }

        return normalized.AsReadOnly();
    }
}