from django.db import models

class MpesaTransaction(models.Model):
    merchant_request_id = models.CharField(max_length=50)
    checkout_request_id = models.CharField(max_length=50)
    result_code = models.IntegerField()
    result_desc = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.BigIntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    
    # New fields to match frontend interface
    payment_type = models.CharField(
        max_length=20, 
        choices=[('product', 'Product'), ('subscription', 'Subscription')],
        default='product'
    )
    product_id = models.IntegerField(null=True, blank=True)
    subscription_plan_id = models.CharField(max_length=50, null=True, blank=True)
    account_reference = models.CharField(max_length=100, null=True, blank=True)
    transaction_desc = models.TextField(null=True, blank=True)
    
    # User tracking
    user_id = models.IntegerField(null=True, blank=True)  # Reference to user who initiated
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.merchant_request_id} - {self.payment_type}"
    
    class Meta:
        ordering = ['-created_at']


class MpesaB2CTransaction(models.Model):
    """Model for B2C (Business to Customer) transactions"""
    conversation_id = models.CharField(max_length=100, unique=True)
    originator_conversation_id = models.CharField(max_length=100)
    response_code = models.CharField(max_length=10)
    response_description = models.TextField()
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=14)
    command_id = models.CharField(max_length=50)  # BusinessPayment, SalaryPayment, PromotionPayment
    remarks = models.TextField()
    occasion = models.CharField(max_length=255)
    
    # Result details (populated by callback)
    result_code = models.IntegerField(null=True, blank=True)
    result_description = models.TextField(null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.CharField(max_length=20, null=True, blank=True)
    transaction_completed_date = models.CharField(max_length=20, null=True, blank=True)
    b2c_utility_account_available_funds = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    b2c_working_account_available_funds = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    b2c_charges_paid_account_available_funds = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    receiver_party_public_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Additional tracking
    user_id = models.IntegerField(null=True, blank=True)  # Reference to user who initiated
    reference = models.CharField(max_length=100, null=True, blank=True)  # Custom reference
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"B2C Transfer: {self.phone_number} - KES {self.amount}"
    
    class Meta:
        ordering = ['-created_at']