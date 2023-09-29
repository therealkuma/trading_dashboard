query_loan_gl=f"""
use MPLConsumerLoansOperationsProd

--Step 1: mapping to Origination
drop table if exists #tapePL;
SELECT 
  serv.MplAcctid
, CRBFundedDate = CAST(orig.CRBFundedDate as DATE)
, PurchaseDate = CAST(orig.PurchaseDate AS DATE)
,orig.CRBDateSold
, OriginalTerm=orig.Term 
, serv.LoanStatus
, serv.DaysPastDue
, orig.LoanAmount
, serv.BeginningBalance
, serv.EndingBalance
, serv.SimpleInterestAccruedLastMonth
, serv.SimpleInterestAccrued
,serv.PrincipalPmt
,serv.InterestPmt
,serv.LateFeePaid
,serv.ChargedOffAmt
,orig.SubpoolID 
,serv.ChargeOffDate
,HFS.IsClassified
,HFS.ClassifiedDate
,orig.DiscountedLoan
,orig.IssuingBankId
INTO #TapePL
FROM MplServicingTapeReporting serv  
JOIN MPLConsumerLoansReporting orig ON orig.LoanNumber=serv.MplAcctId  AND orig.LoanCustomerID = serv.LoanCustomerID
LEFT JOIN MPLConsumerLoansOperationsProd..LoansAllocatedRetainedHFS	HFS
ON HFS.MplAcctId =serv.MplAcctId  AND HFS.LoanCustomerID = serv.LoanCustomerID
WHERE serv.LoanCustomerId=27 
AND serv.ReportDate='2023-09-01' 
and (orig.Category='Retained'  or  serv.isretained = 1)
and orig.IsSold=0   
and orig.IsCanceled =0 and orig.IsRemovedFromFunding =0 and orig.IsReturn =0
--AND orig.IssuingBankId = 'CRB'
--AND CAST(orig.CRBFundedDate as DATE) >='2020-01-01'
AND orig.SubpoolID  IN ( 'PL' ,'PL BRB')

 --- first Tab1 all retained loans
SELECT * FROM #TapePL
ORDER BY CRBFundedDate
""" 
