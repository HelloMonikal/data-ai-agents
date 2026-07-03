from langchain_core.tools import tool
import pandas as pd
 

@tool
def data_checkup(file_path: str) -> str:
    """对一个 CSV 数据文件做质量体检，返回数据诊断报告。
    输入是 CSV 文件的路径（字符串），比如 'sample.csv'。
    报告包含：行列数、每列缺失情况、数值列的基本统计、检测到的异常值。
    当用户想了解一份数据的质量、有什么问题、或需要数据概况时使用。"""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return f"找不到文件: {file_path}"
    except Exception as e:
        return f"读取文件出错: {e}"


    lines = []
    lines.append(f"数据规模: {df.shape[0]} 行, {df.shape[1]} 列")
    lines.append(f"列名: {', '.join(df.columns)}")

    # 缺失值
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        lines.append("缺失值情况:")
        for col, cnt in missing.items():
            pct = cnt / len(df) * 100
            lines.append(f"  - {col}: 缺失 {cnt} 个 ({pct:.1f}%)")
    else:
        lines.append("缺失值情况: 无缺失")

    # 数值列统计
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        lines.append("数值列统计:")
        for col in numeric_cols:
            s = df[col]
            lines.append(
                f"  - {col}: 均值 {s.mean():.2f}, 中位数 {s.median():.2f}, "
                f"标准差 {s.std():.2f}, 范围 [{s.min():.2f}, {s.max():.2f}]"
            )

    # 异常值（IQR 法）
    outlier_found = False
    for col in numeric_cols:
        s = df[col].dropna()
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = s[(s < low) | (s > high)]
        if len(outliers) > 0:
            if not outlier_found:
                lines.append("检测到的异常值 (IQR法):")
                outlier_found = True
            lines.append(
                f"  - {col}: {len(outliers)} 个异常值, "
                f"例如 {list(outliers.head(3).round(2))}"
            )
    if not outlier_found:
        lines.append("异常值: 未检测到明显异常值")

    return "\n".join(lines)