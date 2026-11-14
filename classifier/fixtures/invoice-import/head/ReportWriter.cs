using System;
using System.IO;
using System.Text;
using System.Text.Json;

namespace InvoiceImport;

public static class ReportWriter
{
    public static string Write(BatchReport report)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true }))
        {
            writer.WriteStartObject();
            writer.WriteString("tenant", report.Tenant);
            writer.WriteString("state", report.State);
            writer.WriteNumber("totalRows", report.TotalRows);
            writer.WriteNumber("accepted", report.Accepted);
            writer.WriteNumber("rejected", report.Rejected);
            writer.WriteStartArray("totals");
            foreach (var total in report.Totals)
            {
                writer.WriteStartObject();
                writer.WriteString("currency", total.Currency);
                writer.WriteNumber("net", total.Net);
                writer.WriteNumber("tax", total.Tax);
                writer.WriteNumber("gross", total.Gross);
                writer.WriteEndObject();
            }
            writer.WriteEndArray();

            writer.WriteStartArray("rows");
            foreach (var row in report.Rows)
            {
                writer.WriteStartObject();
                writer.WriteNumber("line", row.Line);
                writer.WriteString("state", row.State);
                if (row.InvoiceId.HasValue)
                {
                    writer.WriteString("invoiceId", row.InvoiceId.Value);
                }
                else
                {
                    writer.WriteNull("invoiceId");
                }

                if (row.State == "accepted")
                {
                    writer.WriteString("currency", row.Currency);
                    writer.WriteNumber("net", row.Net);
                    writer.WriteNumber("tax", row.Tax);
                }

                writer.WriteStartArray("issues");
                foreach (var issue in row.Issues)
                {
                    WriteIssue(writer, issue);
                }
                writer.WriteEndArray();
                writer.WriteEndObject();
            }
            writer.WriteEndArray();

            writer.WriteStartArray("fileIssues");
            foreach (var issue in report.FileIssues)
            {
                WriteIssue(writer, issue);
            }
            writer.WriteEndArray();
            writer.WriteEndObject();
        }

        return Encoding.UTF8.GetString(stream.ToArray());
    }

    private static void WriteIssue(Utf8JsonWriter writer, RowIssue issue)
    {
        writer.WriteStartObject();
        writer.WriteNumber("line", issue.Line);
        writer.WriteString("field", issue.Field);
        writer.WriteString("code", issue.Code);
        writer.WriteString("message", issue.Message);
        writer.WriteEndObject();
    }
}