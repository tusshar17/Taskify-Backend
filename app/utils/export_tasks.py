from io import BytesIO
import pandas as pd


def export_tasks(tasks):
    # convert data to DataFrame
    df = pd.DataFrame(tasks)

    # save to excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Tasks")

    output.seek(0)

    return output
