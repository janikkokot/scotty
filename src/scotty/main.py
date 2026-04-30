import datetime
from typing import NamedTuple
import click
from pyhafas import HafasClient
from pyhafas.profile import VVVProfile
from pyhafas.types.fptf import Mode
from rich import print


def get_client():
    yield HafasClient(VVVProfile())


@click.command("scotty")
@click.option("--origin", type=str, required=True)
@click.option("--destination", type=str, required=True)
@click.option("--change-time", type=int, default=10, show_default=True)
@click.option(
    "--time",
    type=click.DateTime(
        formats=["%Y-%m-%dT%H:%M", "%H:%M"],
    ),
    default=datetime.datetime.now(),
    show_default="NOW",
)
def main(origin, destination, change_time, time):
    client = next(get_client())

    best_origin, *_ = client.locations(origin)
    best_destination, *_ = client.locations(destination)

    journeys = client.journeys(
        origin=best_origin,
        destination=best_destination,
        date=time,
        min_change_time=change_time,
    )
    journey = journeys[0]

    current_date = journey.legs[0].departure.date()

    max_length = max(
        len(getattr(leg, what).name)
        for leg in journey.legs
        for what in "origin destination".split()
    )
    n = 5
    size = (max_length // n + int(bool(max_length % n))) * n
    lines = []
    for leg in journey.legs:
        departure = leg.departure
        fmt = "%H:%M"
        if departure.date() == current_date:
            departure = departure.time()
        else:
            current_date = departure.date()
            fmt = "%m-%d %H:%M"
        departure = format(departure, fmt)
        fmt = "%H:%M"
        arrival = leg.arrival
        if arrival.date() == current_date:
            arrival = arrival.time()
        else:
            current_date = arrival.date()
            fmt = "%m-%d %H:%M"
        arrival = format(arrival, fmt)
        lines.append(
            Row(
                departure=leg.origin.name,
                departure_time=departure,
                arrival=leg.destination.name,
                arrival_time=arrival,
                mode=leg.mode.value if leg.mode is not Mode.WALKING else "foot",
            )
        )

    d_size = max(len(l.departure) for l in lines)
    dt_size = max(len(l.departure_time) for l in lines)
    a_size = max(len(l.arrival) for l in lines)
    at_size = max(len(l.arrival_time) for l in lines)
    m_size = max(len(l.mode) for l in lines)

    for n, line in enumerate(lines):
        msg = [
            "Leave at" if n == 0 else " " * 8,
            rf"[italic blue]{line.departure_time:^{dt_size}}[/italic blue]",
            "from",
            rf"[green]{line.departure:^{d_size}}[/green]",
            rf"by [yellow]{line.mode:^{m_size}}[/yellow] to",
            rf"[green]{line.arrival:^{a_size}}[/green]",
            rf"[italic blue]({line.arrival_time:^{at_size}})[/italic blue]",
        ]
        print(" ".join(msg))


class Row(NamedTuple):
    departure: str
    departure_time: str
    arrival: str
    arrival_time: str
    mode: str


if __name__ == "__main__":
    main()
