//ZTRBR14  JOB (ACCT),'ZTRACTOR',CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//* JCL de teste: ${HLQ} e substituido pelo zTractor antes do submit
//STEP1    EXEC PGM=IEFBR14
//DD1      DD DSN=${HLQ}.ZTRACTOR.TESTE,DISP=(NEW,DELETE),
//            SPACE=(TRK,(1,1)),UNIT=SYSDA
