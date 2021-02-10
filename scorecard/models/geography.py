import logging

from django.db import models
from django.conf import settings
from django.utils.text import slugify
import requests

log = logging.getLogger(__name__)


CATEGORIES = {
    'A': 'metro',
    'B': 'local',
    'C': 'district',
}


class LocationNotFound(Exception):
    pass


class Geography(models.Model):
    #: The level for this geography (eg. `country`) which, together with
    #: `geo_code`, makes up the unique geo id.
    geo_level = models.CharField(max_length=15, null=False)
    #: The code for this geography which must be unique for this level.
    #: Together with `geo_level`, this makes up the unique geo id.
    geo_code = models.CharField(max_length=10, null=False)

    #: Name of this geography.
    name = models.CharField(max_length=100, null=False, db_index=True)
    #: Long name of this geography, giving it context (such as a city or province)
    #: If this is null, it is computed based on the place's ancestors.
    long_name = models.CharField(max_length=100, null=True, db_index=True)

    #: Area in square kilometers. Optional.
    square_kms = models.FloatField(null=True)

    # hierarchy
    #: The level of this geography's parent, or `None` if this is the root
    #: geography that has no parent.
    parent_level = models.CharField(max_length=15, null=True)
    #: The code of this geography's parent, or `None` if this is the root
    #: geography that has no parent.
    parent_code = models.CharField(max_length=10, null=True)

    province_name = models.CharField(max_length=100, null=False)
    province_code = models.CharField(max_length=5, null=False)
    category = models.CharField(max_length=2, null=False)
    miif_category = models.TextField(null=True)
    population = models.IntegerField(null=True)

    postal_address_1 = models.TextField(null=True)
    postal_address_2 = models.TextField(null=True)
    postal_address_3 = models.TextField(null=True)
    street_address_1 = models.TextField(null=True)
    street_address_2 = models.TextField(null=True)
    street_address_3 = models.TextField(null=True)
    street_address_4 = models.TextField(null=True)
    phone_number = models.TextField(null=True)
    fax_number = models.TextField(null=True)
    url = models.TextField(null=True)

    class Meta:
        unique_together = ('geo_level', 'geo_code')
        verbose_name_plural = "Geographies"

    def __str__(self):
        return f'{self.name}'

    @property
    def category_name(self):
        return CATEGORIES[self.category] + ' municipality'

    @property
    def geoid(self):
        return '-'.join([self.geo_level, self.geo_code])

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def parent_geoid(self):
        if self.parent_level and self.parent_code:
            return '%s-%s' % (self.parent_level, self.parent_code)
        return None

    @property
    def parent(self):
        """ The parent of this geograhy, or `None` if this is the root of
        the hierarchy.
        """
        if not hasattr(self, '_parent'):
            if self.parent_level and self.parent_code:
                self._parent = self.__class__.objects.filter(
                    geo_level=self.parent_level, geo_code=self.parent_code).first()
            else:
                self._parent = None

        return self._parent

    def ancestors(self):
        """ A list of the ancestors of this geography, all the way up to the root.
        This is an empty list if this geography is the root of the hierarchy.
        """
        ancestors = []
        g = self.parent
        while g:
            ancestors.append(g)
            g = g.parent
        return ancestors

    def as_dict(self):
        return {
            'ancestors': [a.as_dict() for a in self.ancestors()],
            'full_geoid': self.geoid,
            'full_name': self.long_name,
            'name': self.long_name,
            'short_name': self.name,
            'geo_level': self.geo_level,
            'geo_code': self.geo_code,
            'parent_geoid': self.parent_geoid,
            'square_kms': self.square_kms,
            'province_name': self.province_name,
            'province_code': self.province_code,
            'category': self.category,
            'category_name': self.category_name,
            'miif_category': self.miif_category,
            'slug': self.slug,
        }

    @property
    def bbox(self):
        url = settings.MAPIT['url'] + '/area/MDB:%s/geometry?generation=%s' % (
            self.geo_code, settings.MAPIT['generation'])
        resp = requests.get(url)
        js = resp.json()
        return [js[x] for x in ["min_lon", "min_lat", "max_lon", "max_lat"]]

    def __unicode__(self):
        return self.full_name

    @classmethod
    def find(cls, geo_code, geo_level):
        geo = cls.objects.filter(
            geo_level=geo_level, geo_code=geo_code).first()
        if not geo:
            raise LocationNotFound(
                "Invalid level, code: %s-%s" % (geo_level, geo_code))
        return geo

    @classmethod
    def get_locations_from_coords(cls, longitude, latitude):
        """
        Returns a list of geographies containing this point.
        """
        url = settings.MAPIT['url'] + '/point/4326/%s,%s?generation=%s' % (
            longitude, latitude, settings.MAPIT['generation'])
        resp = requests.get(url)
        resp.raise_for_status()

        geos = []
        for feature in resp.json().values():
            try:
                geo = cls.find(feature['codes']['MDB'],
                               feature['type_name'].lower())

                if geo.geo_level in ['municipality', 'district']:
                    geos.append(geo)
            except LocationNotFound as e:
                log.warn("Couldn't find geo that Mapit gave us: %s" %
                         feature, exc_info=e)

        return geos
