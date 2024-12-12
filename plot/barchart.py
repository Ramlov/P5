import pandas as pd
import plotly.graph_objects as go

# Load CSV file
file_path = "network_metrics.csv"  # Replace with your file path
df = pd.read_csv(file_path)

# Function to generate bar chart and print mismatched rows
def generate_barchart(data, regions_criteria):
    percentages = []
    region_labels = []
    x_labels = []  # Labels for the X-axis
    colors = ["#636EFA", "#d39a69", "#00CC96", "#a2d369"]  # Custom colors for bars
    mismatched_rows = []  # Store rows that do not match

    for region, criteria in regions_criteria.items():
        fd_range = list(map(int, criteria["range"].split('-')))
        status_filter = criteria["status"]
        
        # Filter data for the specified FD range
        filtered_data = data[(data['FD_ID'] >= fd_range[0]) & (data['FD_ID'] <= fd_range[1])]
        
        # Total rows within the FD range
        total_rows = len(filtered_data)
        
        # Filter data for the specified status
        matching_status_data = filtered_data[filtered_data['Status'].str.lower() == status_filter.lower()]
        matching_rows = len(matching_status_data)
        
        # Collect rows that do not match the status
        mismatched_rows.append(filtered_data[filtered_data['Status'].str.lower() != status_filter.lower()])
        
        # Calculate percentage
        percentage = (matching_rows / total_rows) * 100 if total_rows > 0 else 0
        percentages.append(percentage)
        region_labels.append(f"Status: {status_filter} - Percentage: {percentage:.2f}%")
        x_labels.append(f"{region} - {status_filter}")  # Include status in the X-axis label
    
    # Create the Plotly bar chart
    fig = go.Figure()

    for i, (x_label, percentage) in enumerate(zip(x_labels, percentages)):
        fig.add_trace(go.Bar(
            x=[x_label],  # Use labels with status on the X-axis
            y=[percentage],
            name=region_labels[i],  # Simplified legend with status and percentage
            marker_color=colors[i % len(colors)],  # Cycle through custom colors
            opacity=0.8  # Set bar opacity to 80%
        ))
    
    # Update layout for transparent plot and black text
    fig.update_layout(
        title=dict(
            text="Percentage of Rows Matching Status per Region",
            font=dict(size=24, color="black")  # Bigger title text, black color
        ),
        xaxis=dict(
            title="Regions and Status",
            titlefont=dict(size=18, color="black"),  # Bigger X-axis title text, black color
            tickfont=dict(size=14, color="black")  # Bigger X-axis tick text, black color
        ),
        yaxis=dict(
            title="Percentage (%)",
            titlefont=dict(size=18, color="black"),  # Bigger Y-axis title text, black color
            tickfont=dict(size=14, color="black"),  # Bigger Y-axis tick text, black color
            range=[0, 100]  # Set Y-axis limit to 0-100%
        ),
        legend=dict(
            title=dict(
                text="Regions and Status (Percentage)",  # Title of the legend
                font=dict(size=16, color="black")  # Bigger legend title text, black color
            ),
            font=dict(size=14, color="black")  # Bigger legend item text, black color
        ),
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot background
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent paper background
        showlegend=True  # Enable legend
    )

    # Show the chart
    fig.show()

    # Concatenate and print mismatched rows
    if mismatched_rows:
        all_mismatched = pd.concat(mismatched_rows, ignore_index=True)
        print("\nRows that do not match the criteria:")
        print(all_mismatched)


# Example input structure
regions_criteria = {
    "Region 1": {
        "range": "0-14",
        "status": "Good"
    },
    "Region 2": {
        "range": "15-29",
        "status": "Acceptable"
    },
    "Region 3": {
        "range": "30-44",
        "status": "Poor"
    },
    "Region 4": {
        "range": "45-59",
        "status": "Unavailable"
    }
}

# Generate the bar chart and print mismatched rows
generate_barchart(df, regions_criteria)
