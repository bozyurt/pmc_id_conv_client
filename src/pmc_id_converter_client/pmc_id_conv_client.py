import time

import requests
from tqdm import tqdm
from enum import Enum

BASE_URL = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/'


def configure(base_url):
    global BASE_URL
    BASE_URL = base_url


class IDType(Enum):
    PMID = 'pmid'
    PMCID = 'pmcid'
    DOI = 'doi'


class IDConvRequest(object):
    def __init__(self, id_type: IDType = None, versions=False, ids: list[str] = None):
        self.format = 'json'
        self.id_type = id_type
        self.versions = versions
        self.ids = ids

    def get_payload(self):
        id_str = ",".join(self.ids)
        payload = {'ids': id_str, 'format': self.format}
        if not self.versions:
            payload['versions'] = 'no'
        if self.id_type:
            payload['idtype'] = self.id_type.value
        return payload


class IDConvResult(object):
    def __init__(self, requested_id, pmid, pmcid, doi):
        self.requested_id = requested_id
        self.pmid = pmid
        self.pmcid = pmcid
        self.doi = doi

    def __str__(self):
        return f'IDCovResult:: request_id: {self.requested_id} pmid: {self.pmid} pmcid: {self.pmcid} doi: {self.doi}'

    def __repr__(self):
        return f"IDConvResult('{self.requested_id}', '{self.pmid}', '{self.pmcid}', '{self.doi}')"


class PMCIDConverter(object):
    def __init__(self, email):
        self.tool = 'pmc_id_convert_client'
        self.email = email

    def convert_ids(self, request: IDConvRequest):
        max_id_size = 200
        if len(request.ids) < max_id_size:
            return self._convert_ids_chunk(request)
        else:
            chunk_lists = to_chunks(request.ids, max_id_size)
            results = []
            for id_chunk in tqdm(chunk_lists, desc="ID Conversion Progress", unit=" chunks"):
                cr = IDConvRequest(id_type=request.id_type, versions=request.versions, ids=id_chunk)
                rc_list = self._convert_ids_chunk(cr)
                results.extend(rc_list)
                time.sleep(0.5)
            return results

    def _convert_ids_chunk(self, request: IDConvRequest):
        payload = request.get_payload();
        payload['tool'] = self.tool
        payload['email'] = self.email
        r = requests.get(BASE_URL, payload)
        if r.status_code == requests.codes.ok:
            js_dict = r.json()
            results = parse_records(js_dict, request)
            return results
        else:
            if r.status_code == requests.codes.not_found:
                print(r.json())
                return []
            r.raise_for_status()


def to_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def parse_records(_js_dict, request: IDConvRequest):
    results = []
    if 'records' not in _js_dict:
        return results
    req_id_set = None
    if request.id_type and request.id_type == IDType.PMCID:
        req_id_set = set()
        for rid in request.ids:
            if not rid.startswith('PMC'):
                req_id_set.add('PMC' + rid)
            else:
                req_id_set.add(rid)
    else:
        req_id_set = set(request.ids)
    recs = _js_dict['records']
    for rec in recs:
        pmcid, pmid, doi = None, None, None
        if 'pmcid' in rec:
            pmcid = rec['pmcid']
        if 'pmid' in rec:
            pmid = rec['pmid']
        if 'doi' in rec:
            doi = rec['doi']
        requested_id = None
        if pmid in req_id_set:
            requested_id = pmid
        elif pmcid in req_id_set:
            requested_id = pmcid
        elif doi in req_id_set:
            requested_id = doi
        cr = IDConvResult(requested_id, pmid, pmcid, doi)
        results.append(cr)
    return results


if __name__ == '__main__':
    converter = PMCIDConverter(email='iozyurt@health.ucsd.edu')
    ids = ['PMC7611378']
    ids = ['16923184', '28913292', '2794350', '3676833', '33125423']
    req = IDConvRequest(ids=ids)
    res_list = converter.convert_ids(req)
    for r in res_list:
        print(r)

