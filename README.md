# Deep sequencing of the *Haemophilus influenzae* community in bronchiectasis

This repository contains the custom scripts and VCF files used for the SNV analysis described in "Quasispecies behaviour of the Haemophilus influenzae community in the airways of people with bronchiectasis".

Variants were called with GATK HaplotypeCaller, restricted to the *H. influenzae* 86-028NP chromosome, filtered into two separately analysed SNV subsets, and annotated with SnpEff:  
(i) type I SNVs; SNVs supported exclusively by reads carrying the alternative allele (reference allele depth = 0, alternative allele depth > 0. Script: `filter_vcf_only_ALT.py`, and   
(ii) type II SNV; SNVs at positions covered by reads carrying both the reference and the alternative allele (reference allele depth > 0, alternative allele depth > 0). Script: `filter_vcf.py`   

All commands are listed below.

## Pipeline

The steps below were run per sample (`DundeeXXX`). Steps marked *manual* were not scripted.

### 1. Variant calling (GATK)

Input: quality-filtered BAM files (MAPQ ≥ 30, duplicates removed) with index (`.bai`).
Reference: combined database of human, bacterial, archaeal, fungal and viral genomes (`2021_12_human_bact_arch_fungi_vir.fasta`), refer to https://github.com/MHH-RCUG/nf_wochenende

```bash
# Sequence dictionary for the reference
gatk CreateSequenceDictionary -R 2021_12_human_bact_arch_fungi_vir.fa -O 2021_12_human_bact_arch_fungi_vir.dict

# Haploid variant calling
gatk HaplotypeCaller \
  --input DundeeXXX_kneaddata_R1.trm.ns.fix.s.dup.mm.mq30.calmd.bam \
  --output DundeeXXX_out_file_raw_variants.vcf \
  --reference 2021_12_human_bact_arch_fungi_vir.fasta \
  -ploidy 1

# Keep SNPs only
gatk SelectVariants -V DundeeXXX_out_file_raw_variants.vcf \
  -O DundeeXXX_out_file_SNPs.vcf --select-type-to-include SNP

# Restrict to the H. influenzae 86-028NP chromosome
gatk SelectVariants -V DundeeXXX_out_file_SNPs.vcf \
  -O DundeeXXX_out_file_SNPs_Hinflu.vcf \
  -L 1_CP000057_2_Haemophilus_influenzae_86_028NP__complete_genome_BAC
```

### 2. Split into the two SNV subsets (custom Python scripts)

```bash
for file in Dundee*_out_file_SNPs_Hinflu.vcf; do
    python3 filter_vcf_only_ALT.py "$file"   # set (i) -> *_SNPs_Hinflu_ALTonly.vcf
    python3 filter_vcf.py "$file"            # set (ii)  -> *_SNPs_Hinflu_filtered.vcf
done
```


### 3. Clean the VCF header (*manual*)

The VCF header still listed all contigs of the combined reference database. These `##contig` lines were removed.
This also removed the contig line of *H. influenzae*, which bcftools requires. It was re-inserted manually below the `##INFO` block of each file:

```
##contig=<ID=1_CP000057_2_Haemophilus_influenzae_86_028NP__complete_genome_BAC,length=1914490>
```

### 4. Genotype quality filter (bcftools)

```bash
for file in Dundee*_SNP_Hinflu.vcf Dundee*_SNP_Hinflu_ALT.vcf; do
    bcftools view -i 'FORMAT/GQ>=99' "$file" -o "${file%.vcf}_filtGQ.vcf"
done
```

`GQ>=99` keeps only SNVs with the maximum genotype quality.


### 5. Rename the chromosome for SnpEff (bcftools)

The chromosome name was changed to the RefSeq accession used in the SnpEff database. The file `rename_file.txt` contains one tab-separated line:

```
1_CP000057_2_Haemophilus_influenzae_86_028NP__complete_genome_BAC    NC_007146.2
```

```bash
for file in Dundee*_SNP_Hinflu_filtGQ.vcf Dundee*_SNP_Hinflu_ALT_filtGQ.vcf; do
    bcftools annotate --rename-chrs rename_file.txt -o "${file%.vcf}_fixed.vcf" "$file"
done
```

### 6. Custom SnpEff database (once)

No prebuilt SnpEff database was available for *H. influenzae* 86-028NP. A custom database (`Haemophilus_influenzae_custom`) was built from the NCBI RefSeq genome NC_007146.2 (sequence-identical to GenBank CP000057.2, which is part of the GATK reference):

```bash
# in snpEff/data/Haemophilus_influenzae_custom/: sequences.fa and genes.gff (from NCBI)
samtools faidx sequences.fa
gffread -x cds.fa     -g sequences.fa genes.gff
gffread -y protein.fa -g sequences.fa genes.gff

# entry added to snpEff.config:
# Haemophilus_influenzae_custom.genome : Haemophilus influenzae 86-028NP

java -jar snpEff.jar build -gff3 -v Haemophilus_influenzae_custom
```

### 7. Annotation (SnpEff, *manual per sample*)

```bash
java -Xmx4g -jar snpEff.jar -v Haemophilus_influenzae_custom \
  DundeeXXX_SNP_Hinflu_filtGQ_fixed.vcf > DundeeXXX_SNP_Hinflu.ann.vcf

java -Xmx4g -jar snpEff.jar -v Haemophilus_influenzae_custom \
  DundeeXXX_SNP_Hinflu_ALT_filtGQ_fixed.vcf > DundeeXXX_SNP_Hinflu_ALT.ann.vcf
```

After each run, the SnpEff reports (`snpEff_summary.html`, `snpEff_genes.txt`) were renamed with the sample name.

The annotated VCF files were exported to tables with `bcftools query` for further analysis in Excel.  
```bcftools query -f '%CHROM,%POS,%ID,%REF,%ALT,%QUAL,%FILTER,%INFO/ANN\n' DundeeXXX_SNP_Hinflu.ann.vcf```
