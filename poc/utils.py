"""
Whenever we refer to clubs or competitions, we refer to dictionary
holding (possibly modified by user interaction) data about the clubs
or competitions from the JSON files. The keys of those dictionaries are
always strings while the values can be strings, integers, booleans and
even dictionaries.
"""


import json
from flask import flash, render_template
from datetime import datetime
from typing import Union


def load_clubs(path) -> list[dict[str, any]]:
    """Loads the JSON file containing data about the clubs and
    returns it in a list."""
    with open(path) as clubs:
        list_of_clubs = json.load(clubs)['clubs']
        return list_of_clubs


def load_competitions(path) -> list[dict[str, any]]:
    """Loads the JSON file containing data about the competitions and
    returns it in a list."""
    with open(path) as competitions:
        list_of_competitions = json.load(competitions)['competitions']
        return list_of_competitions


def search_club(field: str, value: any, path: str) -> Union[list, tuple[
    dict[str, any], list[dict[str, any]]]]:
    """Loads the JSON file containing data about the clubs and
    returns data about the club having the corresponding field and
    value. For convenience, also returns the list of clubs."""
    if field not in ["name", "email", "points", "reserved_places"]:
        raise ValueError("the value for the field arg isn't a valid one")

    clubs = load_clubs(path)
    try:
        club = [club for club in clubs if club[field] == value][0]
    except IndexError or KeyError:
        return []
    else:
        return club, clubs


def search_competition(field: str, value: any, path: str) -> Union[list, tuple[
    dict[str, any], list[dict[str, any]]]]:
    """Loads the JSON file containing data about the competitions and only
    returns data about the competition having the corresponding field and
    value. For convenience, also returns the list of competitions."""
    if field not in ["name", "date", "number_of_places", "taken_place"]:
        raise ValueError("the value for the field arg isn't a valid one")

    competitions = load_competitions(path)
    try:
        competition = [competition for competition in competitions
                       if competition[field] == value][0]
    except IndexError or KeyError:
        return []
    else:
        return competition, competitions


def update_all_competitions_taken_place_field(
        competitions: list[dict[str, any]],
        competition_path: str) -> list[dict[str, any]]:
    """Receives a list of competitions. Loops through each
    competition. Compares the date field with datetime.now(). Sets
    the taken_place field to True if the date field is behind.
    Writes the list of competitions to the JSON file and returns
    the list."""
    for competition in competitions:
        if datetime.strptime(
                competition["date"], "%Y-%m-%d %H:%M:%S"
        ) <= datetime.now():
            competition["taken_place"] = True
        else:
            competition["taken_place"] = False
            with open(
                    competition_path, "w"
            ) as file_to_write_competitions:
                json.dump({"competitions": competitions},
                          file_to_write_competitions,
                          indent=4)
    return competitions


def more_than_12_reserved_places(club_reserved_places: int,
                                 required_places: int) -> Union[str, None]:
    """Flashes a message if the club did reserve more than 12 places.

    Args:
        club_reserved_places: the number of places the club already reserved at
            the tournament before this operation.
        required_places: the number of places the club wants to reserve at the
            tournament within this operation.

    Returns: A string used in run_checks() if the club tries to reserve more
        than 12 places.
    """
    to_be_reserved_total_places = club_reserved_places + required_places
    if to_be_reserved_total_places > 12:
        flash("you required more than 12 places !")
        return "failed_check"


def not_enough_points(required_places: int,
                      club_number_of_points: int) -> Union[str, None]:
    """Flashes the corresponding message if the club wants to purchase more
    places than they have points.

    Args:
        required_places: the number of places the club wants to reserve at the
            tournament within this operation
        club_number_of_points: the number of points the club has before this
            operation.

    Returns: A string used in run_checks() if the club wants to purchase more
    places than they have points.
    """
    if required_places > club_number_of_points:
        flash("you do not have enough points!")
        return "failed_check"


def no_more_available_places(required_places: int,
                             places_available: int) -> Union[str, None]:
    """Flashes the corresponding message if there aren't enough places at the
    competition.

    Args:
        required_places: the number of places the club wants to reserve at the
            tournament within this operation.
        places_available: the competition's number of available places.
    Returns: A string used in run_checks() if the club wants to purchase
        places although the competition doesn't have places anymore.
    """
    if places_available - required_places < 0:
        flash("there are no more places available !")
        return "failed_check"


def competition_took_place(competition: dict[str, any]) -> Union[str, None]:
    """Flashes the corresponding message if the competition already took place.

    There is already a check when welcome.html is loaded. However, it might be
    the case that after first loading the page, the user is inactive some time
    and then tries to purchase a place. Therefore, a check at that stage is
    also useful.

    Args:
        competition: the competition where the club wants to reserve a place
            within this operation.
    Returns: A string used in run_checks() if the club wants to purchase
        places although the competition already took place.
    """
    if datetime.strptime(
            competition["date"], "%Y-%m-%d %H:%M:%S"
    ) <= datetime.now():
        competition["taken_place"] = True
    else:
        competition["taken_place"] = False
    if competition["taken_place"]:
        flash("the competition already took place !")
        return "failed_check"


def run_checks(competition: dict[str, any], club: dict[str, any],
               required_places: int) -> callable:
    """Makes sure all conditions are met to enable the club to purchase the
    required places at the competition.

    The first unmet condition will trigger a flash message via one of the
    4 functions call. Each function calls checks one condition. If one check
    failed, the following checks aren't done.

    Args:
        competition: the competition where the club wants to purchase places.
        club: the club trying to purchase places.
        required_places: the number of places the club wants to reserve at the
            tournament.

    Returns: A call to render_template. It renders booking.html from the
        templates directory with the club and competition vars as a context.
    """

    failed_checks = more_than_12_reserved_places(
        club["reserved_places"][competition["name"]],
        required_places
    ) or not_enough_points(
        required_places,
        club["points"]
    ) or no_more_available_places(
        required_places,
        competition["number_of_places"]
    ) or competition_took_place(competition)

    if failed_checks:
        return render_template("booking.html",
                               club=club,
                               competition=competition)


def record_changes(competitions: list[dict[str, any]],
                   competition: dict[str, any],
                   clubs: list[dict[str, any]],
                   club: dict[str, any],
                   required_places: int,
                   club_number_of_points: int,
                   competition_path: str,
                   club_path: str
                   ) -> tuple[
                    list[dict[str, any]], dict[str, any]]:
    """Writes two new JSON files to record the changes after the club
     successfully purchased places to the competition.

    Args:
        competitions: all the competitions. Even if only one competition
            was modified, we need to write them all back to the JSON.
        competition: the competition where the club wants to purchase places.
        clubs: all the clubs. Even if only one club
            was modified, we need to write them all back to the JSON.
        club: the club trying to purchase places.
        required_places: the number of places the club wants to reserve at the
            tournament within this operation.
        club_number_of_points: the number of points the club has before this
            operation.
        competition_path: path to the JSON file storing the competitions.
        club_path: path to the JSON file storing the clubs.

    Returns: All the competitions and the club that successfully purchased
        the places. Those dictionaries are used by the render_template call
        returned by server.purchase_places.
    """
    competition_to_be_booked_name = competition["name"]
    competition['number_of_places'] = int(
        competition['number_of_places']
    ) - required_places

    club["points"] = club_number_of_points - required_places

    reserved_places = club["reserved_places"][competition_to_be_booked_name]
    total_reserved_places = reserved_places + required_places
    club["reserved_places"][
        competition_to_be_booked_name] = total_reserved_places
    with open(club_path, "w") as to_be_updated_clubs:
        json.dump({"clubs": clubs},
                  to_be_updated_clubs,
                  indent=4)

    with open(competition_path, "w") as to_be_updated_competitions:
        json.dump({"competitions": competitions},
                  to_be_updated_competitions,
                  indent=4)

    return competitions, club

