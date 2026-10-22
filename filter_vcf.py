import sys

# Ensure the input file is passed as an argument
input_file = sys.argv[1]
output_file = input_file.replace('.vcf', '_filtered.vcf')


with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        if line.startswith('##'):  # Keep metadata lines (##...)
            outfile.write(line)
        elif line.startswith('#CHROM'):  # Keep header line
            outfile.write(line)
        else:
            columns = line.strip().split('\t')
            info_field = columns[7]  # INFO field is the 8th column (index 7)
            format_field = columns[8]  # FORMAT field is the 9th column (index 8)
            sample_field = columns[9]  # Sample data is the 10th column (index 9)

            # Extract AD values (ref and alt allele depth)
            ad_index = format_field.split(':').index('AD')  # Find the index of AD in the FORMAT column
            ad_values = sample_field.split(':')[ad_index]  # Extract AD values for this sample
            ad_counts = list(map(int, ad_values.split(',')))  # Split by comma and convert to integers
            
            if len(ad_counts) >= 2:  # Make sure we have both REF and ALT counts
                ref_count, alt_count = ad_counts[0], ad_counts[1]
                
                # Keep the line if both REF and ALT counts are greater than 0
                if ref_count > 0 and alt_count > 0:
                    outfile.write(line)
