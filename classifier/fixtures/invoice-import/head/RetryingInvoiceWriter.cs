using System;

namespace InvoiceImport;

public sealed class RetryingInvoiceWriter
{
    private readonly IInvoiceStore store;
    private readonly int maximumAttempts;

    public RetryingInvoiceWriter(IInvoiceStore store, int maximumAttempts)
    {
        if (maximumAttempts < 1 || maximumAttempts > 3)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumAttempts));
        }

        this.store = store;
        this.maximumAttempts = maximumAttempts;
    }

    public WriteResult Write(string tenant, NormalizedInvoice row, decimal tax)
    {
        for (int attempt = 1; attempt <= maximumAttempts; attempt++)
        {
            var invoice = new Invoice(
                Guid.NewGuid(),
                tenant,
                row.Supplier,
                row.Number,
                row.Date,
                row.Currency,
                row.Net,
                tax,
                InvoiceStatus.Active);

            try
            {
                store.Save(invoice);
                return new WriteResult(true, invoice.Id, attempt, string.Empty);
            }
            catch (TransientStoreException)
            {
                if (attempt == maximumAttempts)
                {
                    return new WriteResult(false, null, attempt, "Transient store error after bounded retries.");
                }
            }
            catch (InvalidOperationException)
            {
                return new WriteResult(false, null, attempt, "The store rejected the invoice.");
            }
        }

        throw new InvalidOperationException("No write attempt was made.");
    }
}