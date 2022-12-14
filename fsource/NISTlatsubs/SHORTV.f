      SUBROUTINE SHORTV(SXX,SXY,ELEM1,ELEM5,ELEM9,ELEMX)
C**
      COMMON /CK02/ ICK021,ICK022,ICK023,ICK024,ICK025,ICK026,ICK027,
     $              ICK028,ICK029
C*
C
C
C     SUBROUTINE 'SHORTV' ...
C        FOR TWO VECTORS X AND Y, FIND THE SHORTEST Y' RELATIVE TO X
C
C
C**
C     --- FOR CHECKING, WRITE EXECUTION POINT AND INTERMEDIATE VARIABLES
      IF(ICK026.EQ.1) CALL CKPT02(8)
C*
C
C     --- INITIALIZE VARIABLES
      AXY = ABS(SXY)
      XN = 0.0
      IF(SXY.LE.0.0) XN =  1.0
      IF(SXY.GT.0.0) XN = -1.0
      XN1 = 0.0
C
C     --- DETERMINE THE NUMBER OF VECTOR ADDITIONS OR SUBTRACTIONS
C         REQUIRED TO OBTAIN THE SHORTEST Y' RELATIVE TO X.  IF THE
C         INITIAL ANGLE IS < 90 DEGREES, VECTOR X IS SUBTRACTED XN1
C         TIMES, IF THE INITIAL ANGLE IS >= 90 DEGREES, VECTOR X IS
C         ADDED XN1 TIMES.
  100 CONTINUE
      RXY = ABS(SXY + XN*SXX)
      IF((RXY-AXY).GT.0.0) GO TO 160
         IF(SXY.GE.0.0) GO TO 120
            XN  = XN  + 1.0
            XN1 = XN1 + 1.0
            GO TO 140
  120    CONTINUE
         XN  = XN  - 1.0
         XN1 = XN1 - 1.0
  140    CONTINUE
         AXY = RXY
         GO TO 100
  160 CONTINUE
C
C     --- SET THE MATRIX ELEMENTS FOR THE MATRIX USED TO UPDATE
C         THE TOTAL TRANSFORMATION MATRIX (U)
      CALL SET
      ELEM1 = 1.0
      ELEM5 = 1.0
      ELEM9 = 1.0
      ELEMX = XN1
C
      RETURN
      END
