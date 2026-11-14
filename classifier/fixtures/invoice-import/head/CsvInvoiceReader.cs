using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.VisualBasic.FileIO;

namespace InvoiceImport;

public static class CsvInvoiceReader
{
    public static CsvDocument Read(string text, int maximumRows)
    {
        if (maximumRows < 1 || maximumRows > 10000)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumRows));
        }

        var rows = new List<RawInvoiceRow>();
        var issues = new List<RowIssue>();
        if (string.IsNullOrWhiteSpace(text))
        {
            issues.Add(new RowIssue(1, "file", "empty", "The CSV file is empty."));
            return new CsvDocument(rows, issues, false);
        }

        if (text.Length > 1000000)
        {
            issues.Add(new RowIssue(1, "file", "size", "The CSV exceeds the size limit."));
            return new CsvDocument(rows, issues, false);
        }

        using var reader = new StringReader(text.TrimStart('\uFEFF'));
        using var parser = new TextFieldParser(reader);
        parser.TextFieldType = FieldType.Delimited;
        parser.SetDelimiters(",");
        parser.HasFieldsEnclosedInQuotes = true;
        parser.TrimWhiteSpace = false;

        string[] header;
        try
        {
            header = parser.ReadFields();
        }
        catch (MalformedLineException)
        {
            issues.Add(new RowIssue(1, "header", "malformed", "The header is not valid CSV."));
            return new CsvDocument(rows, issues, false);
        }

        var columns = MapHeader(header, issues);
        if (issues.Count > 0)
        {
            return new CsvDocument(rows, issues, false);
        }

        int consumed = 0;
        while (!parser.EndOfData)
        {
            int line = checked((int)parser.LineNumber);
            if (consumed >= maximumRows)
            {
                issues.Add(new RowIssue(line, "file", "row-limit", "The row limit was reached."));
                break;
            }

            consumed++;
            string[] fields;
            try
            {
                fields = parser.ReadFields();
            }
            catch (MalformedLineException)
            {
                issues.Add(new RowIssue(line, "row", "malformed", "The row is not valid CSV."));
                continue;
            }

            if (fields == null || fields.Length != header.Length)
            {
                issues.Add(new RowIssue(line, "row", "column-count", "The row has an unexpected column count."));
                continue;
            }

            rows.Add(new RawInvoiceRow(
                line,
                fields[columns["supplier"]],
                fields[columns["number"]],
                fields[columns["date"]],
                fields[columns["currency"]],
                fields[columns["net"]],
                fields[columns["tax"]]));
        }

        return new CsvDocument(rows.AsReadOnly(), issues.AsReadOnly(), true);
    }

    private static Dictionary<string, int> MapHeader(string[] header, List<RowIssue> issues)
    {
        var columns = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        if (header == null)
        {
            issues.Add(new RowIssue(1, "header", "missing", "A header row is required."));
            return columns;
        }

        for (int index = 0; index < header.Length; index++)
        {
            string name = header[index].Trim();
            if (!columns.TryAdd(name, index))
            {
                issues.Add(new RowIssue(1, name, "duplicate-column", "Header names must be unique."));
            }
        }

        foreach (string required in new[] { "supplier", "number", "date", "currency", "net", "tax" })
        {
            if (!columns.ContainsKey(required))
            {
                issues.Add(new RowIssue(1, required, "missing-column", "A required column is missing."));
            }
        }

        return columns;
    }
}