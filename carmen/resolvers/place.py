"""Resolvers based on Twitter Places."""


from collections import defaultdict
from itertools import count
import re
import warnings

from ..location import Location, EARTH
from ..names import ALTERNATIVE_COUNTRY_NAMES, US_STATE_ABBREVIATIONS


STATE_RE = re.compile(r'.+,\s*(\w+)')


class PlaceResolver(object):
    """A resolver that locates a tweet by matching Twitter Place
    information with a known location.  If *allow_unknown_locations* is
    True, unknown Places are added as new locations.  Otherwise, if
    *resolve_to_known_ancestor* is True, tweets with unknown Places will
    be resolved to the nearest known location containing that Place."""

    name = 'place'

    _unknown_id_start = 1000000

    def __init__(self, allow_unknown_locations=True,
                       resolve_to_known_ancestor=False):
        self.allow_unknown_locations = allow_unknown_locations
        self.resolve_to_known_ancestor = resolve_to_known_ancestor
        self._locations_by_name = {}
        self._unknown_ids = count(self._unknown_id_start)

    def _find_by_name(self, **kwargs):
        return self._locations_by_name.get(Location(**kwargs).canonical())

    def add_location(self, location):
        self._locations_by_name[location.canonical()] = location

    def resolve_tweet(self, tweet):
        place = tweet['place']
        if not place:
            return
        country = place['country']
        if not country:
            warnings.warn('Tweet has Place with no country')
            return None
        country = ALTERNATIVE_COUNTRY_NAMES.get(country.lower(), country)

        name = {'country': country}

        place_type = place['place_type'].lower()
        if place_type in ('neighborhood', 'poi'):
            full_name = place['full_name']
            if full_name:
                split_full_name = full_name.split(',')
                if len(split_full_name) > 1:
                    name['city'] = split_full_name[-1]
            else:
                warnings.warn('Tweet has Place with no neighborhood or '
                              'point of interest full name')
        elif place_type == 'city':
            name['city'] = place['name']
            if country.lower() == 'united states':
                full_name = place['full_name']
                if full_name:
                    # Attempt to extract a state name from the full_name.
                    match = STATE_RE.search(full_name)
                    if match:
                        state = match.group(1).lower()
                        name['state'] = US_STATE_ABBREVIATIONS.get(state)
                else:
                    warnings.warn('Tweet has Place with no city full name')
        elif place_type == 'admin':
            name['state'] = place['name']
        elif place_type == 'country':
            pass
        else:
            warnings.warn('Tweet has unknown place type "%s"' % place_type)
            return None

        location = self._find_by_name(**name)
        if location:
            return (10, location)
        if self.allow_unknown_locations:
            # Remember this location for future lookups.
            location = Location(
                id=next(self._unknown_ids),
                twitter_url=place['url'], twitter_id=place['id'],
                **name)
            self.add_location(location)
            return (10, location)
        if self.resolve_to_known_ancestor:
            ancestor = location
            while True:
                ancestor = ancestor.parent()
                if ancestor == EARTH:
                    break
                known_ancestor = self.id_to_location.get(
                    self.location_to_id.get(ancestor))
                if known_ancestor:
                    return (1, known_ancestor)
        return None
