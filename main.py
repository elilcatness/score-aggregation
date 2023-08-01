import os
from csv import DictReader, DictWriter
from dotenv import load_dotenv

from alive_progress import alive_bar

from src.constants import DELIMITER


def main():
    output_filename = os.getenv('output_filename', 'output.csv')
    initial_data = []
    for key, default in [('volume_filename', 'volume.csv'),
                         ('difficulty_filename', 'difficulty.csv'),
                         ('score_filename', 'score.csv')]:
        filename = os.getenv(key, default)
        try:
            with open(filename, encoding='utf-8') as f:
                first_line = f.readline().strip()
                empty_msg = f'Файл {filename} пуст!'
                if not first_line or not (rows := list(DictReader(
                        f, first_line.split(DELIMITER), delimiter=DELIMITER))):
                    return print(empty_msg)
                initial_data.append(rows)
        except FileNotFoundError:
            return print(f'Файл {filename} не найден!')
    delete_empty = input('Удалять «пустые» значения? (y\\n): ').lower() == 'y'
    data_fieldnames = ['Volume', 'Difficulty', 'Score']
    data = dict()
    for sub_data, data_key in zip(initial_data, data_fieldnames):
        with alive_bar(len(sub_data), title=f'Агрегация {data_key}') as bar:
            for row in sub_data:
                q = row['Запрос']
                for country_key in row:
                    if country_key == 'Запрос':
                        continue
                    country = country_key.split('_')[0]
                    if (key := f'{q}|{country}') not in data:
                        data[key] = {data_key: row[country_key]}
                    else:
                        data[key][data_key] = row[country_key]
                bar()
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        writer = DictWriter(f, ['Query|Country'] + data_fieldnames, delimiter=DELIMITER)
        writer.writeheader()
        count = 0
        with alive_bar(len(data), title=f'Запись в {output_filename}') as bar:
            for key, val in sorted(data.items(), key=lambda t: float(t[1]['Score']), reverse=True):
                if not delete_empty or any(val[sub_key] for sub_key in ('Volume', 'Difficulty')):
                    writer.writerow({'Query|Country': key, **val})
                    count += 1
                bar()
        print(f'Записано строк в {output_filename}: {count}')
        if delete_empty:
            print(f'Отсечено строк: {len(data) - count}')


if __name__ == '__main__':
    load_dotenv()
    main()
