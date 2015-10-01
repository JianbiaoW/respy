!*******************************************************************************
!*******************************************************************************
!
!   This delivers all functions and subroutines to the ROBUFORT library that 
!	are associated with the model under risk. 
!
!*******************************************************************************
!*******************************************************************************
MODULE robufort_emax

	!/*	external modules	*/

    USE robufort_constants

    USE robufort_auxiliary

	!/*	setup	*/

    IMPLICIT NONE

    PUBLIC

CONTAINS
!*******************************************************************************
!*******************************************************************************
SUBROUTINE simulate_emax(emax_simulated, payoffs_ex_post, future_payoffs, & 
                num_periods, num_draws, period, k, eps_relevant_emax, & 
                payoffs_ex_ante, edu_max, edu_start, periods_emax, states_all, & 
                mapping_state_idx, delta)

    !/* external objects    */

    REAL(our_dble), INTENT(OUT)     :: payoffs_ex_post(4)
    REAL(our_dble), INTENT(OUT)     :: emax_simulated
    REAL(our_dble), INTENT(OUT)     :: future_payoffs(4)

    INTEGER(our_int), INTENT(IN)    :: mapping_state_idx(:,:,:,:,:)
    INTEGER(our_int), INTENT(IN)    :: states_all(:,:,:)
    INTEGER(our_int), INTENT(IN)    :: period
    INTEGER(our_int), INTENT(IN)    :: num_periods
    INTEGER(our_int), INTENT(IN)    :: num_draws
    INTEGER(our_int), INTENT(IN)    :: k
    INTEGER(our_int), INTENT(IN)    :: edu_max
    INTEGER(our_int), INTENT(IN)    :: edu_start

    REAL(our_dble), INTENT(IN)      :: eps_relevant_emax(:,:)
    REAL(our_dble), INTENT(IN)      :: payoffs_ex_ante(:)
    REAL(our_dble), INTENT(IN)      :: periods_emax(:,:)
    REAL(our_dble), INTENT(IN)      :: delta

    !/* internals objects    */

    INTEGER(our_int)                :: i

    REAL(our_dble)                  :: total_payoffs(4)
    REAL(our_dble)                  :: disturbances(4)
    REAL(our_dble)                  :: maximum

!-------------------------------------------------------------------------------
! Algorithm
!-------------------------------------------------------------------------------

    ! Initialize containers
    payoffs_ex_post = zero_dble
    emax_simulated = zero_dble

    ! Iterate over Monte Carlo draws
    DO i = 1, num_draws 

        ! Select disturbances for this draw
        disturbances = eps_relevant_emax(i, :)

        ! Calculate total value
        CALL get_total_value(total_payoffs, payoffs_ex_post, future_payoffs, &
                period, num_periods, delta, payoffs_ex_ante, disturbances, &
                edu_max, edu_start, mapping_state_idx, periods_emax, k, states_all)
        
        ! Determine optimal choice
        maximum = MAXVAL(total_payoffs)

        ! Recording expected future value
        emax_simulated = emax_simulated + maximum

    END DO

    ! Scaling
    emax_simulated = emax_simulated / num_draws

END SUBROUTINE
!*******************************************************************************
!*******************************************************************************
SUBROUTINE get_total_value(total_payoffs, payoffs_ex_post, future_payoffs, &
                period, num_periods, delta, payoffs_ex_ante, & 
                disturbances, edu_max, edu_start, mapping_state_idx, & 
                periods_emax, k, states_all)

    !   Development Note:
    !   
    !       The VECTORIZATION supports the inlining and vectorization
    !       preparations in the build process.

    !/* external objects    */

    REAL(our_dble), INTENT(OUT)     :: total_payoffs(4)
    REAL(our_dble), INTENT(OUT)     :: payoffs_ex_post(4)
    REAL(our_dble), INTENT(OUT)     :: future_payoffs(4)

    INTEGER(our_int), INTENT(IN)    :: k
    INTEGER(our_int), INTENT(IN)    :: period
    INTEGER(our_int), INTENT(IN)    :: num_periods
    INTEGER(our_int), INTENT(IN)    :: edu_max
    INTEGER(our_int), INTENT(IN)    :: edu_start
    INTEGER(our_int), INTENT(IN)    :: mapping_state_idx(:, :, :, :, :)
    INTEGER(our_int), INTENT(IN)    :: states_all(:, :, :)

    REAL(our_dble), INTENT(IN)      :: delta
    REAL(our_dble), INTENT(IN)      :: payoffs_ex_ante(:)
    REAL(our_dble), INTENT(IN)      :: disturbances(:)
    REAL(our_dble), INTENT(IN)      :: periods_emax(:, :)

    !/* internals objects    */

    LOGICAL                         :: is_myopic
    
!-------------------------------------------------------------------------------
! Algorithm
!-------------------------------------------------------------------------------
    
    ! Initialize containers
    payoffs_ex_post = zero_dble

    ! Auxiliary objects
    is_myopic = (delta .EQ. zero_dble)

    ! Calculate ex post payoffs
    payoffs_ex_post(1) = payoffs_ex_ante(1) * disturbances(1)
    payoffs_ex_post(2) = payoffs_ex_ante(2) * disturbances(2)
    payoffs_ex_post(3) = payoffs_ex_ante(3) + disturbances(3)
    payoffs_ex_post(4) = payoffs_ex_ante(4) + disturbances(4)

    ! Get future values
    ! BEGIN VECTORIZATION A
    IF (period .NE. (num_periods - one_int)) THEN
        CALL get_future_payoffs(future_payoffs, edu_max, edu_start, & 
                mapping_state_idx, period,  periods_emax, k, states_all)
        ELSE
            future_payoffs = zero_dble
    END IF
    ! END VECTORIZATION A

    ! Calculate total utilities
    total_payoffs = payoffs_ex_post + delta * future_payoffs

    ! Stabilization in case of myopic agents
    IF (is_myopic .EQV. .TRUE.) THEN
        CALL stabilize_myopic(total_payoffs, future_payoffs)
    END IF

END SUBROUTINE
!*******************************************************************************
!*******************************************************************************
SUBROUTINE get_future_payoffs(future_payoffs, edu_max, edu_start, &
                mapping_state_idx, period, periods_emax, k, states_all)

    !/* external objects    */

    REAL(our_dble), INTENT(OUT)     :: future_payoffs(4)

    INTEGER(our_int), INTENT(IN)    :: k
    INTEGER(our_int), INTENT(IN)    :: period
    INTEGER(our_int), INTENT(IN)    :: edu_max
    INTEGER(our_int), INTENT(IN)    :: edu_start
    INTEGER(our_int), INTENT(IN)    :: states_all(:, :, :)
    INTEGER(our_int), INTENT(IN)    :: mapping_state_idx(:, :, :, :, :)

    REAL(our_dble), INTENT(IN)      :: periods_emax(:, :)

    !/* internals objects    */

    INTEGER(our_int)    			:: exp_A
    INTEGER(our_int)    			:: exp_B
    INTEGER(our_int)    			:: edu
    INTEGER(our_int)    			:: edu_lagged
    INTEGER(our_int)    			:: future_idx

!-------------------------------------------------------------------------------
! Algorithm
!-------------------------------------------------------------------------------

    ! Distribute state space
    exp_A = states_all(period + 1, k + 1, 1)
    exp_B = states_all(period + 1, k + 1, 2)
    edu = states_all(period + 1, k + 1, 3)
    edu_lagged = states_all(period + 1, k + 1, 4)

	! Working in occupation A
    future_idx = mapping_state_idx(period + 1 + 1, exp_A + 1 + 1, & 
                    exp_B + 1, edu + 1, 1)
    future_payoffs(1) = periods_emax(period + 1 + 1, future_idx + 1)

	!Working in occupation B
    future_idx = mapping_state_idx(period + 1 + 1, exp_A + 1, &
                    exp_B + 1 + 1, edu + 1, 1)
    future_payoffs(2) = periods_emax(period + 1 + 1, future_idx + 1)

	! Increasing schooling. Note that adding an additional year
	! of schooling is only possible for those that have strictly
	! less than the maximum level of additional education allowed.
    IF (edu < edu_max - edu_start) THEN
        future_idx = mapping_state_idx(period + 1 + 1, exp_A + 1, &
                        exp_B + 1, edu + 1 + 1, 2)
        future_payoffs(3) = periods_emax(period + 1 + 1, future_idx + 1)
    ELSE
        future_payoffs(3) = -HUGE(future_payoffs)
    END IF

	! Staying at home
    future_idx = mapping_state_idx(period + 1 + 1, exp_A + 1, & 
                    exp_B + 1, edu + 1, 1)
    future_payoffs(4) = periods_emax(period + 1 + 1, future_idx + 1)

END SUBROUTINE
!*******************************************************************************
!*******************************************************************************
SUBROUTINE stabilize_myopic(total_payoffs, future_payoffs)


    !/* external objects    */

    REAL(our_dble), INTENT(INOUT)   :: total_payoffs(:)
    REAL(our_dble), INTENT(IN)      :: future_payoffs(:)

    !/* internals objects    */

    LOGICAL                         :: is_huge

!-------------------------------------------------------------------------------
! Algorithm
!-------------------------------------------------------------------------------
    
    ! Determine NAN
    is_huge = (future_payoffs(3) == -HUGE(future_payoffs))

    IF (is_huge .EQV. .True.) THEN
        total_payoffs(3) = -HUGE(future_payoffs)
    END IF

END SUBROUTINE
!*******************************************************************************
!*******************************************************************************
END MODULE