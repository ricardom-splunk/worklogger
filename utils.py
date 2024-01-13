def _convert_duration(duration):
    """Convert the duration string to a format that JIRA likes

    Args:
        duration (str): Format: "HH:MM"

    Returns:
        str: Example: "1w 3d 7h 24m"
    """
    # Split the duration string into hours, minutes, and seconds
    # Expects input as "hh:mm:ss"
    hours, minutes = map(int, duration.split(':'))

    # Convert hours to days, taking into account 1d equals 8h
    days, hours = divmod(hours, 8)

    # Convert days to weeks, taking into account 1w equals 5d
    weeks, days = divmod(days, 5)

    # Construct the formatted duration string
    formatted_duration = ""
    if weeks:
        formatted_duration += f"{weeks}w "
    if days:
        formatted_duration += f"{days}d "
    if hours:
        formatted_duration += f"{hours}h "
    if minutes:
        formatted_duration += f"{minutes}m"

    return formatted_duration.strip()
