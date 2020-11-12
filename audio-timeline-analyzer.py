#!/usr/bin/env python3

import getopt, sys, csv
from os import path
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

def next_to_key(row, key):
    return row[row.index(key) + 1]

class TimelineElement:
    def __init__(self, row):
        self.host_timestamp = int(next_to_key(row, "m_nHostTimestamp:"))
        self.position = int(next_to_key(row, "m_nStreamPosition:"))
        self.number_of_samples = int(next_to_key(row, "m_nNumberOfSamples:"))
        self.forced_silence = bool(next_to_key(row, "m_bIsForcedSilence:"))

class TimelineStep:
    def __init__(self, current, previous, samplerate, clock_resolution):
        self.time_window = current.host_timestamp - previous.host_timestamp
        self.samples = current.position - previous.position
        self.note = ""
        if self.samples != previous.number_of_samples:
            print(f"error: stream position increment {self.samples} at position {previous.position} does not match reported number of samples {previous.number_of_samples}", file=sys.stderr)
            self.note = f"invalid position increment ({self.samples} vs {previous.number_of_samples})"
        self.timestamp = previous.host_timestamp
        self.nominal_samplerate = int(samplerate)
        if self.time_window > 0:
            self.actual_samplerate = self.samples * 1.0 / (self.time_window / clock_resolution)
        else:
            self.actual_samplerate = 0
            note = f"invalid time increment {self.time_window} at timestamp {self.timestamp}"
            print(f"error: {note}", file=sys.stderr)
            if len(self.note):
                self.note = self.note + "\n"
            self.note = self.note + note

def series_from_timeline(iterator, nominal_input_samplerate, clock_resolution):
    previous = TimelineElement(next(iterator))
    series = []
    try:
        while True:
            current = TimelineElement(next(iterator))
            step = TimelineStep(current, previous, nominal_input_samplerate, clock_resolution)
            series.append(step)
            previous = current
    except StopIteration:
        pass
    return series

def split_timeline(timeline):
    time = []
    samplerate = []
    time_delta = []
    note = []
    previous_timestamp = 0
    for entry in timeline:
        time.append(entry.timestamp)
        note.append(entry.note)
        if previous_timestamp == 0:
            time_delta.append(0)
        else:
            time_delta.append(entry.timestamp - previous_timestamp)
        previous_timestamp = entry.timestamp
        samplerate.append(entry.actual_samplerate)
    return time, samplerate, time_delta, note

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:r:", [])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)
    input_file_path = ""
    output_file_path = ""
    # Defaults the clock resolution to nanoseconds
    clock_resolution = 1000 * 1000 * 1000
    for o, a in opts:
        if o == "-i":
            input_file_path = a
        elif o in ("-o"):
            output_file_path = a
        elif o in ("-r"):
            clock_resolution = a
        else:
            assert False, "unhandled option"
    if (not (input_file_path and output_file_path)):
        if (input_file_path):
            if (path.isfile(input_file_path) == False):
                print(f"{input_file_path} does not exist")
                sys.exit(1)
            output_file_path = input_file_path.replace("InputTimeline", "OutputTimeline")
        elif (output_file_path):
            if (path.isfile(output_file_path) == False):
                print(f"{output_file_path} does not exist")
                sys.exit(1)
            input_file_path = output_file_path.replace("InputTimeline", "OutputTimeline")
    if (path.isfile(input_file_path) == False):
        print(f"{input_file_path} does not exist")
        sys.exit(1)
    if (path.isfile(output_file_path) == False):
        print(f"{output_file_path} does not exist")
        sys.exit(1)
    with open(input_file_path, newline='') as input_file:
        with open(output_file_path, newline='') as output_file:
            input_timeline = csv.reader(input_file, delimiter=',')
            output_timeline = csv.reader(output_file, delimiter=',')
            input_header = next(input_timeline)
            output_header = next(output_timeline)
            nominal_input_samplerate = next_to_key(input_header, "Samplerate:")
            nominal_output_samplerate = next_to_key(output_header, "Samplerate:")

            # Iterate through both lists and try to align based on host timestamp
            input_series = series_from_timeline(input_timeline, nominal_input_samplerate, clock_resolution)
            output_series = series_from_timeline(output_timeline, nominal_output_samplerate, clock_resolution)
            input_time, input_rate, input_time_delta, input_note = split_timeline(input_series)
            output_time, output_rate, output_time_delta, output_note = split_timeline(output_series)

            first_time = min(input_time[0], output_time[0])
            last_time = max(input_time[-1], output_time[-1])
            frames = []
            columns = 4
            # Write input/output to an excel file
            max_range = (last_time - first_time) / (clock_resolution / 1000)
            frames.append({"name": "input",
                "data": pd.DataFrame({"Input Timestamp": input_time, "Input Timestamp Delta": input_time_delta, "Input Nominal Sample Rate": input_rate, "Note": input_note}),
                "length": len(input_time)
            })
            frames.append({"name": "output",
                "data": pd.DataFrame({"Output Timestamp": output_time, "Output Timestamp Delta": output_time_delta, "Output Nominal Sample Rate": output_rate, "Note": output_note}),
                "length": len(output_time)
            })
            writer = ExcelWriter("timeline.xlsx", engine="xlsxwriter")
            series = 0
            timeline_sheet = writer.book.add_worksheet("Timeline")
            writer.sheets["Timeline"] = timeline_sheet
            graph_sheet = writer.book.add_worksheet("Sample Rate Drift")
            writer.sheets["Sample Rate Drift"] = graph_sheet
            sample_rate_drift_chart = writer.book.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
            sample_rate_drift_chart.set_x_axis({"name": "Time", "min": first_time, "max": last_time})
            sample_rate_drift_chart.set_y_axis({"name": "Nominal Sample Rate"})
            for frame in frames:
                frame_data = frame["data"]
                frame_data.to_excel(writer, "Timeline", index=False, startcol=series * columns, float_format = "%0.2f")
                end_row = frame["length"] + 1
                sample_rate_drift_chart.add_series({
                    "name": frame["name"],
                    "categories": ["Timeline", 1, series * columns, end_row, series * columns],
                    "values" : ["Timeline", 1, series * columns + 2, end_row, series * columns + 2]
                })
                series += 1

            sample_rate_drift_chart.set_size({"width": max_range, "height": 400})
            graph_sheet.insert_chart(0, 0, sample_rate_drift_chart)
            writer.save()

if __name__ == "__main__":
    main()