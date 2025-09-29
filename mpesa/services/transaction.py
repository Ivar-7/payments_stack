"""
M-Pesa Transaction Service
Unified transaction management and queries
"""
from django.db.models import Q
from ..models import MpesaTransaction, MpesaB2CTransaction


class TransactionService:
    
    def get_user_transactions(self, user_id, transaction_type=None, limit=50):
        """
        Get transactions for a specific user
        
        Args:
            user_id: User ID
            transaction_type: 'stk_push', 'b2c_transfer', or None for all
            limit: Maximum number of transactions to return
        """
        transactions = []
        
        if transaction_type is None or transaction_type == 'stk_push':
            # Get STK Push transactions
            stk_filter = Q()
            if user_id:
                stk_filter &= Q(user_id=user_id)
            
            stk_transactions = MpesaTransaction.objects.filter(stk_filter).order_by('-created_at')[:limit]
            
            for txn in stk_transactions:
                transactions.append({
                    'id': txn.id,
                    'type': 'stk_push',
                    'status': self._get_stk_status(txn),
                    'amount': float(txn.amount) if txn.amount else None,
                    'phone_number': txn.phone_number,
                    'payment_type': txn.payment_type,
                    'product_id': txn.product_id,
                    'mpesa_receipt_number': txn.mpesa_receipt_number,
                    'transaction_date': txn.transaction_date,
                    'result_desc': txn.result_desc,
                    'created_at': txn.created_at.isoformat(),
                    'updated_at': txn.updated_at.isoformat()
                })
        
        if transaction_type is None or transaction_type == 'b2c_transfer':
            # Get B2C transactions
            b2c_transactions = MpesaB2CTransaction.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:limit]
            
            for txn in b2c_transactions:
                transactions.append({
                    'id': txn.id,
                    'type': 'b2c_transfer',
                    'status': self._get_b2c_status(txn),
                    'amount': float(txn.amount),
                    'phone_number': txn.phone_number,
                    'command_id': txn.command_id,
                    'remarks': txn.remarks,
                    'occasion': txn.occasion,
                    'mpesa_receipt_number': txn.mpesa_receipt_number,
                    'transaction_date': txn.transaction_date,
                    'result_description': txn.result_description,
                    'created_at': txn.created_at.isoformat(),
                    'updated_at': txn.updated_at.isoformat()
                })
        
        # Sort by created_at descending
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return transactions[:limit]
    
    def get_transaction_summary(self, user_id=None, days=30):
        """
        Get transaction summary statistics
        
        Args:
            user_id: User ID (None for all users)
            days: Number of days to look back
        """
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        # STK Push summary
        stk_filter = Q(created_at__gte=start_date)
        if user_id:
            stk_filter &= Q(user_id=user_id)
        
        stk_transactions = MpesaTransaction.objects.filter(stk_filter)
        stk_successful = stk_transactions.filter(result_code=0)
        stk_total_amount = sum(float(t.amount) for t in stk_successful if t.amount)
        
        # B2C summary
        b2c_filter = Q(created_at__gte=start_date)
        if user_id:
            b2c_filter &= Q(user_id=user_id)
        
        b2c_transactions = MpesaB2CTransaction.objects.filter(b2c_filter)
        b2c_successful = b2c_transactions.filter(result_code=0)
        b2c_total_amount = sum(float(t.amount) for t in b2c_successful)
        
        return {
            'period_days': days,
            'stk_push': {
                'total_transactions': stk_transactions.count(),
                'successful_transactions': stk_successful.count(),
                'total_amount': stk_total_amount,
                'success_rate': (stk_successful.count() / stk_transactions.count() * 100) if stk_transactions.count() > 0 else 0
            },
            'b2c_transfer': {
                'total_transactions': b2c_transactions.count(),
                'successful_transactions': b2c_successful.count(),
                'total_amount': b2c_total_amount,
                'success_rate': (b2c_successful.count() / b2c_transactions.count() * 100) if b2c_transactions.count() > 0 else 0
            },
            'overall': {
                'total_transactions': stk_transactions.count() + b2c_transactions.count(),
                'successful_transactions': stk_successful.count() + b2c_successful.count(),
                'net_amount': stk_total_amount - b2c_total_amount  # Money in - Money out
            }
        }
    
    def search_transactions(self, query, user_id=None, limit=50):
        """
        Search transactions by phone number, receipt number, or reference
        
        Args:
            query: Search query
            user_id: User ID to filter by (optional)
            limit: Maximum results
        """
        transactions = []
        
        # Search STK transactions
        stk_filter = Q(
            Q(phone_number__icontains=query) |
            Q(mpesa_receipt_number__icontains=query) |
            Q(account_reference__icontains=query)
        )
        if user_id:
            stk_filter &= Q(user_id=user_id)
        
        stk_results = MpesaTransaction.objects.filter(stk_filter).order_by('-created_at')[:limit]
        
        for txn in stk_results:
            transactions.append({
                'id': txn.id,
                'type': 'stk_push',
                'status': self._get_stk_status(txn),
                'amount': float(txn.amount) if txn.amount else None,
                'phone_number': txn.phone_number,
                'mpesa_receipt_number': txn.mpesa_receipt_number,
                'account_reference': txn.account_reference,
                'created_at': txn.created_at.isoformat()
            })
        
        # Search B2C transactions
        b2c_filter = Q(
            Q(phone_number__icontains=query) |
            Q(mpesa_receipt_number__icontains=query) |
            Q(reference__icontains=query) |
            Q(remarks__icontains=query)
        )
        if user_id:
            b2c_filter &= Q(user_id=user_id)
        
        b2c_results = MpesaB2CTransaction.objects.filter(b2c_filter).order_by('-created_at')[:limit]
        
        for txn in b2c_results:
            transactions.append({
                'id': txn.id,
                'type': 'b2c_transfer',
                'status': self._get_b2c_status(txn),
                'amount': float(txn.amount),
                'phone_number': txn.phone_number,
                'mpesa_receipt_number': txn.mpesa_receipt_number,
                'reference': txn.reference,
                'remarks': txn.remarks,
                'created_at': txn.created_at.isoformat()
            })
        
        # Sort by created_at descending
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return transactions[:limit]
    
    def get_failed_transactions(self, user_id=None, limit=50):
        """
        Get failed transactions for troubleshooting
        """
        transactions = []
        
        # Failed STK transactions
        stk_filter = Q(result_code__isnull=False) & ~Q(result_code=0)
        if user_id:
            stk_filter &= Q(user_id=user_id)
        
        failed_stk = MpesaTransaction.objects.filter(stk_filter).order_by('-created_at')[:limit]
        
        for txn in failed_stk:
            transactions.append({
                'id': txn.id,
                'type': 'stk_push',
                'amount': float(txn.amount) if txn.amount else None,
                'phone_number': txn.phone_number,
                'result_code': txn.result_code,
                'result_desc': txn.result_desc,
                'created_at': txn.created_at.isoformat()
            })
        
        # Failed B2C transactions
        b2c_filter = Q(result_code__isnull=False) & ~Q(result_code=0)
        if user_id:
            b2c_filter &= Q(user_id=user_id)
        
        failed_b2c = MpesaB2CTransaction.objects.filter(b2c_filter).order_by('-created_at')[:limit]
        
        for txn in failed_b2c:
            transactions.append({
                'id': txn.id,
                'type': 'b2c_transfer',
                'amount': float(txn.amount),
                'phone_number': txn.phone_number,
                'result_code': txn.result_code,
                'result_description': txn.result_description,
                'created_at': txn.created_at.isoformat()
            })
        
        # Sort by created_at descending
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return transactions[:limit]
    
    def _get_stk_status(self, transaction):
        """Get STK transaction status"""
        if transaction.result_code is None:
            return "pending"
        elif transaction.result_code == 0:
            return "success"
        else:
            return "failed"
    
    def _get_b2c_status(self, transaction):
        """Get B2C transaction status"""
        if transaction.result_code is None:
            return "pending"
        elif transaction.result_code == 0:
            return "success"
        else:
            return "failed"