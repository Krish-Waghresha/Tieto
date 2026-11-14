using System;

namespace HarborOrders;

public static class Checkout
{
    public static string Place(Order order, User user, object shippingProvider)
    {
        if (!Access.CanSubmit(user, order))
        {
            throw new UnauthorizedAccessException();
        }

        decimal total = Pricing.Total(order) + Shipping.Quote(order, shippingProvider);
        return Receipt.Format(order, total);
    }
}