import re


def query(cypher, parameters=None, **kwargs):
    cypher = query.re.sub(' ', cypher.replace('\n', ' '))
    out = {'statement': cypher}
    if parameters is not None:
        out['parameters'] = parameters

    out.update(kwargs)
    return out


query.re = re.compile(r'\s{2,}')
