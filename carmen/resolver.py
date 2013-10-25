"""Main location resolution classes and methods."""


from .location import Location, EARTH


class LocationResolver(object):
    """A "supervising" resolver that attempts to resolve a tweet's
    location by using multiple child resolvers and returning the
    resolution with the highest priority."""

    def __init__(self, resolvers=[]):
        self.resolvers = resolvers
        self.add_location(EARTH)

    def add_location(self, location):
        # Inform our child resolvers of this location.
        for resolver_ in self.resolvers:
            resolver_.add_location(location)

    def resolve_tweet(self, tweet):
        best_resolution = (-1, None)
        best_resolver_name = None
        for resolver_ in self.resolvers:
            resolution = resolver_.resolve_tweet(tweet)
            if resolution > best_resolution:
                best_resolution = resolution
                best_resolver_name = resolver_.name
        location = best_resolution[1]
        if location:
            location.resolution_method = best_resolver_name
        return location
