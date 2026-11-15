using System;
using System.Globalization;
using System.Linq;

namespace InvoiceImport.Tests;

public static class AccountingChecks
{
    private static readonly string[] Normalizer = { "InvoiceNormalizer.cs" };
    private static readonly string[] Validator = { "InvoiceValidator.cs" };

    public static void Run()
    {
        Checks.Run("money.invariant-culture", "INV-102", Normalizer, () =>
        {
            CultureInfo previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("fi-FI");
                Checks.True(InvoiceNormalizer.TryMoney("1234.56", out decimal value), "Invariant decimal should parse.");
                Checks.Equal(1234.56m, value);
                Checks.Equal(false, InvoiceNormalizer.TryMoney("1234,56", out value));
            }
            finally
            {
                CultureInfo.CurrentCulture = previous;
            }
        });

        foreach (string invalid in new[] { "", " ", "1,000", "1e3", "NaN", "Infinity", "12.12345", "--1", "1.2.3", "EUR10", "79228162514264337593543950336" })
        {
            string captured = invalid;
            Checks.Run("money.reject:" + captured, "INV-102", Normalizer, () =>
            {
                Checks.Equal(false, InvoiceNormalizer.TryMoney(captured, out decimal value));
            });
        }

        Checks.Run("money.round-half-away", "INV-102", Normalizer, () =>
        {
            Checks.Equal(1.01m, InvoiceNormalizer.RoundMoney(1.005m));
            Checks.Equal(-1.01m, InvoiceNormalizer.RoundMoney(-1.005m));
            Checks.Equal(1.00m, InvoiceNormalizer.RoundMoney(1.004m));
        });

        Checks.Run("money.normalized-record", "INV-102", Normalizer, () =>
        {
            var raw = new RawInvoiceRow(7, " North Harbor ", " inv-17 ", "2026-11-01", " eur ", "100.005", "20.004");
            NormalizationResult result = InvoiceNormalizer.Normalize(raw);
            Checks.Equal(0, result.Issues.Count);
            Checks.Equal(7, result.Value.Line);
            Checks.Equal("NORTH HARBOR", result.Value.Supplier);
            Checks.Equal("INV-17", result.Value.Number);
            Checks.Equal("EUR", result.Value.Currency);
            Checks.Equal(100.01m, result.Value.Net);
            Checks.Equal(20.00m, result.Value.Tax.Value);
        });

        Checks.Run("money.optional-tax", "INV-102", Normalizer, () =>
        {
            RawInvoiceRow raw = CsvInvoiceReader.Read(Samples.Header + Samples.Row(tax: ""), 10).Rows.Single();
            Checks.Equal(false, InvoiceNormalizer.Normalize(raw).Value.Tax.HasValue);
        });

        Checks.Run("money.negative-before-rounding", "INV-102", Normalizer, () =>
        {
            foreach (var amounts in new[] { (Net: "-0.001", Tax: "0"), (Net: "100", Tax: "-0.001") })
            {
                var raw = new RawInvoiceRow(2, "Harbor", "INV-1", "2026-11-01", "EUR", amounts.Net, amounts.Tax);
                var result = InvoiceNormalizer.Normalize(raw);
                Checks.Equal(null, result.Value);
                Checks.True(result.Issues.Any(issue => issue.Code == "negative"), "A tiny negative amount must not round into a valid zero.");
            }
        });

        Checks.Run("money.unicode-key", "INV-102", Normalizer, () =>
        {
            Checks.Equal(InvoiceNormalizer.NormalizeKey("CAF\u00c9"), InvoiceNormalizer.NormalizeKey("cafe\u0301"));
            Checks.Equal(string.Empty, InvoiceNormalizer.NormalizeKey(null));
        });

        Checks.Run("money.iso-date-only", "INV-102", Normalizer, () =>
        {
            var raw = new RawInvoiceRow(2, "Harbor", "INV", "01/11/2026", "EUR", "100", "20");
            NormalizationResult result = InvoiceNormalizer.Normalize(raw);
            Checks.Equal(null, result.Value);
            Samples.HasIssue(result.Issues, "date", "format");
        });

        Checks.Run("money.error-aggregation", "INV-102", Normalizer, () =>
        {
            var raw = new RawInvoiceRow(2, "Harbor", "INV", "bad", "EUR", "bad", "bad");
            NormalizationResult result = InvoiceNormalizer.Normalize(raw);
            Checks.Equal(3, result.Issues.Count);
            Checks.Equal(null, result.Value);
        });

        Checks.Run("money.batch-order", "INV-102", Normalizer, () =>
        {
            var document = CsvInvoiceReader.Read(Samples.Header + Samples.Row("INV-2") + Samples.Row("INV-1"), 10);
            var normalized = InvoiceNormalizer.NormalizeAll(document.Rows);
            Checks.Equal("INV-2", normalized[0].Value.Number);
            Checks.Equal("INV-1", normalized[1].Value.Number);
        });

        Checks.Run("validation.valid-zero", "INV-103", Validator, () =>
        {
            Checks.Equal(0, InvoiceValidator.Validate(Samples.Normalized(net: 0m, tax: 0m), Samples.Today).Count);
        });

        Checks.Run("validation.amount-boundaries", "INV-103", Validator, () =>
        {
            Checks.Equal(0, InvoiceValidator.Validate(Samples.Normalized(net: 1000000m), Samples.Today).Count);
            Samples.HasIssue(InvoiceValidator.Validate(Samples.Normalized(net: 1000000.01m), Samples.Today), "net", "range");
            Samples.HasIssue(InvoiceValidator.Validate(Samples.Normalized(net: -0.01m), Samples.Today), "net", "range");
        });

        Checks.Run("validation.tax-boundaries", "INV-103", Validator, () =>
        {
            Checks.Equal(0, InvoiceValidator.ValidateTax(2, 100m, 100m).Count);
            Samples.HasIssue(InvoiceValidator.ValidateTax(2, 100m, 100.01m), "tax", "range");
            Samples.HasIssue(InvoiceValidator.ValidateTax(2, 100m, -0.01m), "tax", "negative");
            Samples.HasIssue(InvoiceValidator.ValidateTax(2, 100m, 1.001m), "tax", "precision");
        });

        Checks.Run("validation.date-boundaries", "INV-103", Validator, () =>
        {
            var invoice = Samples.Normalized();
            Checks.Equal(0, InvoiceValidator.Validate(invoice with { Date = Samples.Today }, Samples.Today).Count);
            Checks.Equal(0, InvoiceValidator.Validate(invoice with { Date = new DateOnly(2000, 1, 1) }, Samples.Today).Count);
            Samples.HasIssue(InvoiceValidator.Validate(invoice with { Date = Samples.Today.AddDays(1) }, Samples.Today), "date", "future");
            Samples.HasIssue(InvoiceValidator.Validate(invoice with { Date = new DateOnly(1999, 12, 31) }, Samples.Today), "date", "too-old");
        });

        foreach (string currency in new[] { "EUR", "USD", "GBP" })
        {
            string captured = currency;
            Checks.Run("validation.currency:" + captured, "INV-103", Validator, () =>
            {
                Checks.Equal(0, InvoiceValidator.Validate(Samples.Normalized() with { Currency = captured }, Samples.Today).Count);
            });
        }

        Checks.Run("validation.unsupported-currency", "INV-103", Validator, () =>
        {
            Samples.HasIssue(InvoiceValidator.Validate(Samples.Normalized() with { Currency = "XYZ" }, Samples.Today), "currency", "unsupported");
        });

        Checks.Run("validation.identifier-limits", "INV-103", Validator, () =>
        {
            var invoice = Samples.Normalized() with { Supplier = new string('S', 120), Number = new string('N', 64) };
            Checks.Equal(0, InvoiceValidator.Validate(invoice, Samples.Today).Count);
            var invalid = invoice with { Supplier = new string('S', 121), Number = new string('N', 65) };
            Checks.Equal(2, InvoiceValidator.Validate(invalid, Samples.Today).Count);
        });

        Checks.Run("validation.required-identifiers", "INV-103", Validator, () =>
        {
            var invoice = Samples.Normalized() with { Supplier = "", Number = " " };
            var issues = InvoiceValidator.Validate(invoice, Samples.Today);
            Samples.HasIssue(issues, "supplier", "required");
            Samples.HasIssue(issues, "number", "required");
        });

        Checks.Run("validation.control-characters", "INV-103", Validator, () =>
        {
            var invoice = Samples.Normalized() with { Supplier = "A\nB", Number = "A\u001fB" };
            Checks.Equal(2, InvoiceValidator.Validate(invoice, Samples.Today).Count);
        });

        Checks.Run("validation.missing-tax-deferred", "INV-103", Validator, () =>
        {
            Checks.Equal(0, InvoiceValidator.Validate(Samples.Normalized(tax: null), Samples.Today).Count);
        });
    }
}