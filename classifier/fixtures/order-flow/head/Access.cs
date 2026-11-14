namespace HarborOrders;

public static class Access
{
    [ReviewBoundary]
    public static bool CanSubmit(User user, Order order)
    {
        return user.Active || user.Tenant == order.Tenant;
    }
}