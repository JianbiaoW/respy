import numpy as np

from respy.python.shared.shared_auxiliary import dist_class_attributes
from respy.python.shared.shared_constants import DATA_LABELS_EST


def check_dataset_est(data_frame, respy_obj):
    """ This routine runs some consistency checks on the simulated data frame.
    """
    # Distribute class attributes
    num_periods, edu_spec = dist_class_attributes(respy_obj, 'num_periods', 'edu_spec')

    # Check that there are not missing values in any of the columns but for the wages information.
    for label in DATA_LABELS_EST:
        if label == 'Wage':
            continue
        assert ~ data_frame[label].isnull().any()

    # Checks for PERIODS. It can happen that the last period is deleted for all agents. Thus,
    # this is not a strict equality for observed data. It is for simulated data.
    dat = data_frame['Period']
    np.testing.assert_equal(dat.max() <= num_periods - 1, True)

    # Checks for CHOICE
    dat = data_frame['Choice'].isin([1, 2, 3, 4])
    np.testing.assert_equal(dat.all(), True)

    # Checks for WAGE
    dat = data_frame['Wage'].fillna(99) > 0.00
    np.testing.assert_equal(dat.all(), True)

    # Checks for EXPERIENCE. We also know that both need to take value of zero in the very first
    # period.
    for label in ['Experience_A', 'Experience_B']:
        dat = data_frame[label] >= 0.00
        np.testing.assert_equal(dat.all(), True)

        dat = data_frame[label][:, 0] == 0
        np.testing.assert_equal(dat.all(), True)

    # We check individual state variables against the recorded choices
    data_frame.groupby('Identifier').apply(check_state_variables)

    # Checks for LAGGED ACTIVITY. We also know that all individuals were in school when entering
    # the model. Just to be sure, we also construct the correct lagged activity here as well and
    # compare it to the one provided in the dataset.
    dat = data_frame['Lagged_Activity'].isin(range(4))
    np.testing.assert_equal(dat.all(), True)

    dat = data_frame['Lagged_Activity'][:, 0] == 1
    np.testing.assert_equal(dat.all(), True)

    data_frame['TEMP'] = data_frame.groupby(level='Identifier')['Choice'].shift(+1)
    data_frame['TEMP'] = data_frame['TEMP'].map({1: 2, 2: 3, 3: 1, 4: 0})
    data_frame['TEMP'].loc[:, 0] = 1
    data_frame['TEMP'] = data_frame['TEMP'].astype(int)
    np.testing.assert_equal(data_frame['TEMP'].equals(data_frame['Lagged_Activity']), True)
    del data_frame['TEMP']

    # Checks for YEARS SCHOOLING. We also know that the initial years of schooling can only take
    # values specified in the initialization file.
    dat = data_frame['Years_Schooling'] >= 0.00
    np.testing.assert_equal(dat.all(), True)

    dat = data_frame['Years_Schooling'][:, 0].isin(edu_spec['start'])
    np.testing.assert_equal(dat.all(), True)

    # Check that there are no duplicated observations for any period by agent.
    def check_unique_periods(group):
        np.testing.assert_equal(group['Period'].duplicated().any(), False)
    data_frame.groupby('Identifier').apply(check_unique_periods)

    # Check that we observe the whole sequence of observations and that they are in the right order.
    def check_series_observations(group):
        np.testing.assert_equal(group['Period'].tolist(), list(range(group['Period'].max() + 1)))
    data_frame.groupby('Identifier').apply(check_series_observations)


def check_state_variables(agent):
    """ This function constructs the experience and schooling levels implied by the
    reported choices and compares them to the information provided in the dataset.
    """
    for index, row in agent.iterrows():
        identifier, period = index
        choice = row['Choice']
        # We know that the level of experience is zero in the initial period and we get the
        # initial level of schooling.
        if period == 0:
            exp_a, exp_b, edu = 0.0, 0.0, row['Years_Schooling']
        # Check statistics
        for pair in [(exp_a, 'Experience_A'), (exp_b, 'Experience_B'), (edu, 'Years_Schooling')]:
            stat, label = pair
            np.testing.assert_equal(stat, row[label])
        # Update experience statistics.
        if choice == 1:
            exp_a += 1
        elif choice == 2:
            exp_b += 1
        elif choice == 3:
            edu += 1
        else:
            pass
