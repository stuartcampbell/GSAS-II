      SUBROUTINE DOLLASE(CA,RAT,CORR)

!PURPOSE: Calculate MArch-Dollase function

      INCLUDE       '../INCLDS/COPYRIGT.FOR' 

!PSEUDOCODE:

!CALLING ARGUMENTS:

      REAL*8        CA                  !Cos(alpha)**2
      REAL*8        RAT                 !PO ellipsoid axis ratio
      REAL*8        CORR                !March-Dollase function

!INCLUDE STATEMENTS:

!LOCAL VARIABLES:

      REAL*8        SA                  !Sin(alpha)**2
      REAL*8        A                   !Intermediate value

!SUBROUTINES CALLED:

!FUNCTION DEFINITIONS:

!DATA STATEMENTS:

!CODE:

      SA = 1.0-CA
      A = CA*RAT**2+SA/RAT
      A = 1.0/SQRT(A)
      CORR = A**3
      RETURN
      END
