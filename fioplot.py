#!/usr/bin/env python

import argparse
import datetime
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

    data.insert(0, {'time': 0, 'value': 0})

    df = pd.DataFrame(data)
    dt = pd.to_datetime(df.time, unit='ms')
    df['time'] = dt.dt.time
    df.set_index('time', inplace=True)
    df = df.groupby(['time'])['value'].sum().reset_index()

    if log_type == 'bw':
        df['value'] = df.apply(lambda x: x['value'] / 1024, axis=1)
    if log_type in ['lat', 'slat', 'clat']:
        df['value'] = df.apply(lambda x: x['value'] / 1000000, axis=1)

    # Dataframe Visualization with Pandas Plot
    # https://kanoki.org/2019/09/16/dataframe-visualization-with-pandas-plot/

    xmax = df['time'].max()
    ymax = int(df['value'].max())

    def santize(t):
        return datetime.time(t.hour, t.minute, t.second)

    time_ranges = pd.date_range(start=dt.min(), end=dt.max(), freq='30S').time
    value_ranges = [0, 10, 20, 50]

    df.plot(kind='line', x='time', y='value', title=fn, legend=False, figsize=(15, 9),
            xlim=(0, xmax), ylim=(0, ymax),
            xticks=list(map(santize, time_ranges)),
            yticks=value_ranges.extend([w*100 for w in range(ymax)]),
            rot=30)

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
