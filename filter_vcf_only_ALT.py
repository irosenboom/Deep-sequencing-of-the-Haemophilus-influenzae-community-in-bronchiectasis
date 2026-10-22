import sys

input_file = sys.argv[1]
output_file = input_file.replace('.vcf', '_ALTonly.vcf')

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        if line.startswith('##') or line.startswith('#CHROM'):
            outfile.write(line)
            continue

        columns = line.strip().split('\t')
        format_field = columns[8]
        sample_field = columns[9]

        # Find AD index
        ad_index = format_field.split(':').index('AD')
        ad_values = sample_field.split(':')[ad_index]
        ad_counts = list(map(int, ad_values.split(',')))

        if len(ad_counts) >= 2:
            ref_count, alt_count = ad_counts[:2]

            # Keep if REF = 0 and ALT > 0
            if ref_count == 0 and alt_count > 0:
                outfile.write(line)
