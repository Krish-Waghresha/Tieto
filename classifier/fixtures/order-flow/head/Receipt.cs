using System.Globalization;

namespace HarborOrders;

public static class Receipt
{
    public static string Format(Order order, decimal total)
    {
        return "Order " + order.Id
            + ": " + total.ToString("0.00", CultureInfo.InvariantCulture);
    }
}