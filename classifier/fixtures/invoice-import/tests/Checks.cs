using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;

namespace InvoiceImport.Tests;

public static class Checks
{
    private static readonly List<object> results = new List<object>();
    private static int failed;

    public static void Run(string id, string requirement, string[] covers, Action test)
    {
        var timer = Stopwatch.StartNew();
        string status = "passed";
        string detail = "Assertions passed.";
        try
        {
            test();
        }
        catch (Exception error)
        {
            status = "failed";
            detail = error.GetType().Name + ": " + error.Message;
            failed++;
        }

        results.Add(new { id, requirements = new[] { requirement }, covers, status, detail, milliseconds = timer.Elapsed.TotalMilliseconds });
    }

    public static void Equal<Value>(Value expected, Value actual)
    {
        if (!EqualityComparer<Value>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException($"Expected {expected}; observed {actual}.");
        }
    }

    public static void True(bool value, string message)
    {
        if (!value)
        {
            throw new InvalidOperationException(message);
        }
    }

    public static void Throws<Error>(Action action) where Error : Exception
    {
        try
        {
            action();
        }
        catch (Error)
        {
            return;
        }

        throw new InvalidOperationException("Expected " + typeof(Error).Name);
    }

    public static int Finish()
    {
        Console.WriteLine(JsonSerializer.Serialize(new { tests = results, passed = results.Count - failed, failed }, new JsonSerializerOptions { WriteIndented = true }));
        return failed == 0 ? 0 : 1;
    }
}

public static class Samples
{
    public const string Header = "supplier,number,date,currency,net,tax\n";
    public static readonly DateOnly Today = new DateOnly(2026, 11, 14);

    public static string Row(string number = "INV-1", string net = "100", string tax = "20", string currency = "EUR")
    {
        return "North Harbor," + number + ",2026-11-01," + currency + "," + net + "," + tax + "\n";
    }

    public static NormalizedInvoice Normalized(int line = 2, decimal net = 100m, decimal? tax = 20m)
    {
        return new NormalizedInvoice(line, "NORTH HARBOR", "INV-1", new DateOnly(2026, 11, 1), "EUR", net, tax);
    }

    public static Invoice Existing(string tenant = "tenant-a", InvoiceStatus status = InvoiceStatus.Active)
    {
        return new Invoice(Guid.NewGuid(), tenant, "NORTH HARBOR", "INV-1", Today, "EUR", 100m, 20m, status);
    }

    public static void HasIssue(IEnumerable<RowIssue> issues, string field, string code)
    {
        Checks.True(issues.Any(issue => issue.Field == field && issue.Code == code), "Missing issue " + field + ":" + code);
    }
}

public static class Program
{
    public static int Main()
    {
        ParsingChecks.Run();
        AccountingChecks.Run();
        ReportingChecks.Run();
        WorkflowChecks.Run();
        return Checks.Finish();
    }
}