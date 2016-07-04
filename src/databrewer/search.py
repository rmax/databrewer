import json
import logging

from whoosh.analysis import FancyAnalyzer, StemFilter
from whoosh.fields import Schema, ID, TEXT
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser
from whoosh.query import Query, Variations


DEFAULT_SCHEMA = Schema(
    id=ID(unique=True, stored=True),
    data=ID(stored=True),
    content=TEXT(FancyAnalyzer() | StemFilter()),
)


logger = logging.getLogger(__name__)


class SearchIndex(object):

    def __init__(self, index_dir, schema=DEFAULT_SCHEMA, force_create=False):
        self.schema = schema
        if exists_in(index_dir) and not force_create:
            self.index = open_dir(index_dir, schema=schema)
        else:
            self.index = create_in(index_dir, schema=schema)

    @classmethod
    def is_empty(cls, index_dir):
        si = SearchIndex(index_dir)
        return si.index.is_empty()

    def search(self, query, search_field='content'):
        if not isinstance(query, Query):
            parser = QueryParser(search_field, self.schema, termclass=Variations)
            query = parser.parse(query)

        with self.index.searcher() as searcher:
            for hit in searcher.search(query, limit=100):
                yield self._decode(hit['data'])

    def get(self, key, field='id'):
        kwargs = {field: key}
        hit = self.index.searcher().document(**kwargs)
        if hit:
            return self._decode(hit['data'])

    def list(self):
        for hit in self.index.searcher().documents():
            yield self._decode(hit['data'])

    def update(self, recipes,
               id_field='name',
               text_fields=('name', 'description', 'keywords')):
        writer = self.index.writer()
        for recipe in recipes:
            writer.update_document(
                id=recipe[id_field],
                content=self._get_content(recipe, text_fields),
                data=self._encode(recipe),
            )
        writer.commit(optimize=True)

    def _get_content(self, doc, fields):
        content = []
        for f in fields:
            text = doc.get(f)
            if isinstance(text, list):
                content.extend(text)
            elif text:
                content.append(text)
        return "\n".join(content)

    def _encode(self, obj):
        return json.dumps(obj)

    def _decode(self, data):
        return json.loads(data)
