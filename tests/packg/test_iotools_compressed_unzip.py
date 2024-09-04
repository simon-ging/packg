import datetime

from packg.iotools.compress import read_unzip_list_output


def test_read_unzip_list_output():
    output_str = """\
Archive:  meta_1.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
 20877542  2023-12-31 00:43   curated_ct_report_path_En.csv
 22340136  2023-12-31 00:43   BIMCV_meta.csv
 19077344  2023-12-31 00:43   curated_pos_ct_report_path_En.csv
  2134903  2023-12-31 00:43   curated_neg_ct_report_path_En.csv
 21448178  2024-02-09 02:16   BIMCV_meta_cyd.csv
  1912800  2023-12-31 00:43   mutliCls_meta.csv
---------                     -------
175581806                     12 files\
"""
    output_dict = read_unzip_list_output(output_str)

    gt_dict = {
        "curated_ct_report_path_En.csv": (20877542, 1703979780.0, "2023-12-31 00:43:00"),
        "BIMCV_meta.csv": (22340136, 1703979780.0, "2023-12-31 00:43:00"),
        "curated_pos_ct_report_path_En.csv": (19077344, 1703979780.0, "2023-12-31 00:43:00"),
        "curated_neg_ct_report_path_En.csv": (2134903, 1703979780.0, "2023-12-31 00:43:00"),
        "BIMCV_meta_cyd.csv": (21448178, 1707441360.0, "2024-02-09 02:16:00"),
        "mutliCls_meta.csv": (1912800, 1703979780.0, "2023-12-31 00:43:00"),
    }

    for file, (size, mtime) in output_dict.items():
        time_formatted = datetime.datetime.fromtimestamp(mtime)
        print(f"{file} {size//1024**2:.1f}MB {time_formatted}")
        gt_size, gt_mtime, gt_time_formatted = gt_dict[file]
        assert size == gt_size
        assert abs(mtime - gt_mtime) < 1e-1
        assert str(time_formatted) == gt_time_formatted
