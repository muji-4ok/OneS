# OneS

Идея: считаем расстояние Левенштейна двух от массивов данных
файлов и минимальный путь редакций. В диффе
просто сериализуем все INSERT, DELETE и REPLACE операции
чтобы потом их проиграть

Время работы calculate_diff - O(nm), где n, m - размеры
файлов.

Время работы apply_patch - O(n + d), где n, d - размеры
входного файла и патча
