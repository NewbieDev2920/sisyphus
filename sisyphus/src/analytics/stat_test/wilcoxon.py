def scipy.stats import wilcoxon


def wilcoxon_test(series : pd.Series):
    """
        Wilcoxon test for 0
    """
    stat, p_value = wilcoxon(series)
    return p_value