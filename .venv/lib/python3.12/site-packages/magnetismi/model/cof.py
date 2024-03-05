import importlib.resources
import math
import pathlib

from magnetismi import ENCODING

CS = ('n', 'm', 'gnm', 'hnm', 'dgnm', 'dhnm')
STORE_PATH = pathlib.Path('magnetismi', 'model')
TWIN_END_TOKEN = '9' * 48

YEARS_COVERED = tuple(y for y in range(2020, 2025 + 1))
MODEL_FROM_YEAR = {y: '2020' for y in range(2020, 2025 + 1)}


class Coefficients:
    """The WMM coefficients relevant to the year given."""

    model = {}

    def load(self, model_year: int) -> None:
        """Load the model."""
        model_resource = f'wmm-{model_year}.txt'
        with importlib.resources.path(__package__, model_resource) as model_path:
            with open(model_path, 'rt', encoding=ENCODING) as handle:
                recs = [line.strip().split() for line in handle if line.strip() and line.strip() != TWIN_END_TOKEN]

        epoc, model, model_date_string = recs[0]
        self.model['epoch'] = float(epoc)
        self.model['model_code'] = model
        self.model['model_date_string'] = model_date_string

        self.model['coeffs'] = [
            {c: int(r[s]) if c in ('n', 'm') else float(r[s]) for s, c in enumerate(CS)}
            for r in recs[1:]
            if len(r) == len(CS)
        ]

    def _zeroes(self, count: int) -> list[float]:
        """Short and sweet."""
        return [0.0 for _ in range(count)]

    def evaluate(self) -> None:
        """Ja, ja, ja!"""
        self.maxord = self.maxdeg = 12
        self.tc = [self._zeroes(13) for _ in range(14)]
        self.sp = self._zeroes(14)
        self.cp = self._zeroes(14)
        self.cp[0] = 1.0
        self.pp = self._zeroes(13)
        self.pp[0] = 1.0
        self.p = [self._zeroes(14) for _ in range(14)]
        self.p[0][0] = 1.0
        self.dp = [self._zeroes(13) for _ in range(14)]
        self.a = 6378.137
        self.b = 6356.7523142
        self.re = 6371.2
        self.a2 = self.a * self.a
        self.b2 = self.b * self.b
        self.c2 = self.a2 - self.b2
        self.a4 = self.a2 * self.a2
        self.b4 = self.b2 * self.b2
        self.c4 = self.a4 - self.b4

        self.c = [self._zeroes(14) for _ in range(14)]
        self.cd = [self._zeroes(14) for _ in range(14)]

        for wmmnm in self.model['coeffs']:
            m = wmmnm['m']
            n = wmmnm['n']
            gnm = wmmnm['gnm']
            hnm = wmmnm['hnm']
            dgnm = wmmnm['dgnm']
            dhnm = wmmnm['dhnm']
            if m <= n:
                self.c[m][n] = gnm
                self.cd[m][n] = dgnm
                if m != 0:
                    self.c[n][m - 1] = hnm
                    self.cd[n][m - 1] = dhnm

        # Convert Schmidt normalized Gauss coefficients to unnormalized
        self.snorm = [self._zeroes(13) for _ in range(13)]
        self.snorm[0][0] = 1.0
        self.k = [self._zeroes(13) for _ in range(13)]
        self.k[1][1] = 0.0
        self.fn = [float(n) for n in range(14) if n != 1]
        self.fm = [float(n) for n in range(13)]
        for n in range(1, self.maxord + 1):
            self.snorm[0][n] = self.snorm[0][n - 1] * (2.0 * n - 1) / n
            j = 2.0
            # for (m=0,D1=1,D2=(n-m+D1)/D1;D2>0;D2--,m+=D1):
            m = 0
            D1 = 1
            D2 = (n - m + D1) / D1
            while D2 > 0:
                self.k[m][n] = (((n - 1) * (n - 1)) - (m * m)) / ((2.0 * n - 1) * (2.0 * n - 3.0))
                if m > 0:
                    flnmj = ((n - m + 1.0) * j) / (n + m)
                    self.snorm[m][n] = self.snorm[m - 1][n] * math.sqrt(flnmj)
                    j = 1.0
                    self.c[n][m - 1] = self.snorm[m][n] * self.c[n][m - 1]
                    self.cd[n][m - 1] = self.snorm[m][n] * self.cd[n][m - 1]
                self.c[m][n] = self.snorm[m][n] * self.c[m][n]
                self.cd[m][n] = self.snorm[m][n] * self.cd[m][n]
                D2 = D2 - 1
                m = m + D1

    def __init__(self, year: int):
        """Initialize the mode from file in case it covers the requested year."""
        if year not in YEARS_COVERED:
            raise ValueError(f'requested year ({year}) not within {YEARS_COVERED}')

        self.model = {
            'year_requested': year,
            'model_id': MODEL_FROM_YEAR[year],
        }
        self.load(self.model['model_id'])
        self.evaluate()
