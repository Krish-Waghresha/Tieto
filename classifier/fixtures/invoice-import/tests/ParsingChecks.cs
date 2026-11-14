using System;
using System.Linq;

namespace InvoiceImport.Tests;

public static class ParsingChecks
{
    private static readonly string[] Files = { "CsvInvoiceReader.cs" };

    public static void Run()
    {
        Checks.Run("csv.basic", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(Samples.Header + Samples.Row(), 100);
            Checks.True(document.HeaderValid, "Header should be recognized.");
            Checks.Equal(1, document.Rows.Count);
            Checks.Equal(0, document.Issues.Count);
            Checks.Equal(2, document.Rows[0].Line);
            Checks.Equal("North Harbor", document.Rows[0].Supplier);
        });

        Checks.Run("csv.quoted-comma", "INV-101", Files, () =>
        {
            string csv = Samples.Header + "\"Harbor, North\",INV-1,2026-11-01,EUR,100,20\n";
            CsvDocument document = CsvInvoiceReader.Read(csv, 100);
            Checks.Equal("Harbor, North", document.Rows.Single().Supplier);
        });

        Checks.Run("csv.escaped-quote", "INV-101", Files, () =>
        {
            string csv = Samples.Header + "\"Harbor \"\"North\"\"\",INV-1,2026-11-01,EUR,100,20\n";
            Checks.Equal("Harbor \"North\"", CsvInvoiceReader.Read(csv, 100).Rows.Single().Supplier);
        });

        Checks.Run("csv.multiline-field", "INV-101", Files, () =>
        {
            string csv = Samples.Header + "\"Harbor\nNorth\",INV-1,2026-11-01,EUR,100,20\n" + Samples.Row("INV-2");
            CsvDocument document = CsvInvoiceReader.Read(csv, 100);
            Checks.Equal(2, document.Rows.Count);
            Checks.Equal("Harbor\nNorth", document.Rows[0].Supplier);
            Checks.Equal(4, document.Rows[1].Line);
        });

        Checks.Run("csv.reordered-header", "INV-101", Files, () =>
        {
            string csv = "tax,net,currency,date,number,supplier\n20,100,EUR,2026-11-01,INV-1,North Harbor\n";
            RawInvoiceRow row = CsvInvoiceReader.Read(csv, 100).Rows.Single();
            Checks.Equal("100", row.Net);
            Checks.Equal("INV-1", row.Number);
        });

        Checks.Run("csv.case-insensitive-header", "INV-101", Files, () =>
        {
            string csv = " SUPPLIER ,Number,DATE,Currency,NET,Tax\n" + Samples.Row();
            Checks.True(CsvInvoiceReader.Read(csv, 100).HeaderValid, "Header names are case insensitive.");
        });

        Checks.Run("csv.missing-header", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read("supplier,number\nHarbor,INV-1\n", 100);
            Checks.Equal(false, document.HeaderValid);
            Samples.HasIssue(document.Issues, "net", "missing-column");
        });

        Checks.Run("csv.duplicate-header", "INV-101", Files, () =>
        {
            string csv = "supplier,number,date,currency,net,tax,NET\n";
            CsvDocument document = CsvInvoiceReader.Read(csv, 100);
            Checks.Equal(false, document.HeaderValid);
            Checks.True(document.Issues.Any(issue => issue.Code == "duplicate-column"), "Repeated headers must fail.");
        });

        Checks.Run("csv.additional-column", "INV-101", Files, () =>
        {
            string csv = Samples.Header.TrimEnd('\n') + ",comment\n" + Samples.Row().TrimEnd('\n') + ",ignored\n";
            CsvDocument document = CsvInvoiceReader.Read(csv, 100);
            Checks.Equal(1, document.Rows.Count);
            Checks.Equal("INV-1", document.Rows[0].Number);
        });

        Checks.Run("csv.bad-row-isolation", "INV-101", Files, () =>
        {
            string csv = Samples.Header + "broken,row\n" + Samples.Row("VALID");
            CsvDocument document = CsvInvoiceReader.Read(csv, 100);
            Checks.Equal(1, document.Rows.Count);
            Checks.Equal("VALID", document.Rows[0].Number);
            Checks.Equal(3, document.Rows[0].Line);
            Samples.HasIssue(document.Issues, "row", "column-count");
        });

        Checks.Run("csv.blank-lines", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(Samples.Header + "\n" + Samples.Row(), 100);
            Checks.Equal(1, document.Rows.Count);
        });

        Checks.Run("csv.bom", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read("\uFEFF" + Samples.Header + Samples.Row(), 100);
            Checks.True(document.HeaderValid, "UTF-8 BOM must not corrupt the first header.");
        });

        Checks.Run("csv.crlf", "INV-101", Files, () =>
        {
            string csv = (Samples.Header + Samples.Row()).Replace("\n", "\r\n");
            Checks.Equal(1, CsvInvoiceReader.Read(csv, 100).Rows.Count);
        });

        Checks.Run("csv.no-final-newline", "INV-101", Files, () =>
        {
            string csv = (Samples.Header + Samples.Row()).TrimEnd('\n');
            Checks.Equal("20", CsvInvoiceReader.Read(csv, 100).Rows.Single().Tax);
        });

        Checks.Run("csv.empty", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(string.Empty, 100);
            Checks.Equal(false, document.HeaderValid);
            Samples.HasIssue(document.Issues, "file", "empty");
        });

        Checks.Run("csv.size-limit", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(new string('x', 1000001), 100);
            Checks.Equal(false, document.HeaderValid);
            Samples.HasIssue(document.Issues, "file", "size");
        });

        Checks.Run("csv.row-limit", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(Samples.Header + Samples.Row() + Samples.Row("SECOND"), 1);
            Checks.Equal(1, document.Rows.Count);
            Samples.HasIssue(document.Issues, "file", "row-limit");
        });

        Checks.Run("csv.limit-configuration", "INV-101", Files, () =>
        {
            Checks.Throws<ArgumentOutOfRangeException>(() => CsvInvoiceReader.Read(Samples.Header, 0));
            Checks.Throws<ArgumentOutOfRangeException>(() => CsvInvoiceReader.Read(Samples.Header, 10001));
        });

        Checks.Run("csv.malformed-header", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read("\"unterminated\n", 10);
            Checks.Equal(false, document.HeaderValid);
            Samples.HasIssue(document.Issues, "header", "malformed");
        });

        Checks.Run("csv.malformed-row", "INV-101", Files, () =>
        {
            CsvDocument document = CsvInvoiceReader.Read(Samples.Header + "\"unterminated\n", 10);
            Checks.Equal(0, document.Rows.Count);
            Samples.HasIssue(document.Issues, "row", "malformed");
        });
    }
}