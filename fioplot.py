#!/usr/bin/env python

import argparse
import glob
import re
import os
import pandas as pd
import matplotlib.pyplot as plt


def plot(log, out_dir):
    def get_type(types, fn):
        for t in types:
            expr = r'.*_{0}(?:\.\d+)?\.log$'.format(t)
            pattern = re.compile(expr)
            if pattern.match(fn):
                return t
        return None

    log_types = {
        'iops': 'IOPS',
        'bw': 'MiB/sec',
        'lat': 'lat in msecs',
        'slat': 'slat in msecs',
        'clat': 'clat in msecs'
    }

    fn = os.path.basename(log)
    log_type = get_type(list(log_types.keys()), fn)
    if log_type is None:
        return

    data = []
    with open(log, 'r') as f:
        for l in f:
            # https://fio.readthedocs.io/en/latest/fio_doc.html#log-file-formats
            fields = l.strip().split(',')
            data.append({
                'time': int(fields[0].strip()),
                'value': int(fields[1].strip())
            })
    if not data:
        return

    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df.time, unit='ms').dt.time
    df.set_index('time', inplace=True)
    df = df.groupby(['time'])['value'].sum().reset_index()

    if log_type == 'bw':
        df['value'] = df.apply(lambda x: x['value'] / 1024, axis=1)
    if log_type in ['lat', 'slat', 'clat']:
        df['value'] = df.apply(lambda x: x['value'] / 1000000, axis=1)

    df.plot(kind='line', x='time', y='value', title=fn, legend=False)

    # save plot to image
    fn = os.path.splitext(fn)[0]
    fn = os.path.join(out_dir, '{0}.png'.format(fn))
    plt.xlabel('time')
    plt.ylabel(log_types[log_type])
    plt.savefig(fn)


def main():
    parser = argparse.ArgumentParser(description='Plot fio logs')

    parser.add_argument('-p', dest='pattern', required=True,
                        help='Pattern for fio log files')
    parser.add_argument('-o', dest='out_dir', required=True,
                        help='Dir for output plots')

    args = parser.parse_args()

    logs = glob.glob(os.path.expanduser(args.pattern))
    for log in logs:
        print('handling {0}..'.format(log))
        plot(log, args.out_dir)


if __name__ == "__main__":
    main()
