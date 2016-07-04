

class Dataset(object):
    """Dataset definition base class.
    """

    homepage = None
    description = None
    keywords = None


    def to_pandas(self):
        raise NotImplementedError


class CorpusTexmex(Dataset):

    homepage = 'http://corpus-texmex.irisa.fr/'
    description = """

    """


class DatasetFile(object):

    url =
