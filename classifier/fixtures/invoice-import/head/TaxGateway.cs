using System;

namespace InvoiceImport;

public static class TaxGateway
{
    public static decimal Resolve(NormalizedInvoice invoice, object provider)
    {
        if (invoice.Tax.HasValue)
        {
            return invoice.Tax.Value;
        }

        if (provider == null)
        {
            throw new InvalidOperationException("No tax provider was supplied.");
        }

        dynamic adapter = provider;
        decimal rate = (decimal)adapter.RateFor(invoice.Currency, invoice.Date);
        decimal tax = InvoiceNormalizer.RoundMoney(invoice.Net * rate);
        if (InvoiceValidator.ValidateTax(invoice.Line, invoice.Net, tax).Count > 0)
        {
            throw new InvalidOperationException("The tax provider returned an unsupported rate.");
        }

        return tax;
    }
}