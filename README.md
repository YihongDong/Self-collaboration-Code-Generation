# Self-collaboration Code Generation via ChatGPT
[![arXiv](https://img.shields.io/badge/arXiv-2304.07590-b31b1b.svg)](https://arxiv.org/abs/2304.07590)

The first LLM-based agent for (Function-Level and Project-Level) code generation in software engineering, released in April 2023, has been accepted to TOSEM.

### Function-Level Generation 
```bash
# Generate function-level code
bash run.sh
# Evaluate results
bash evaluate.sh
```

### Project-Level Generation
```bash
# Generate project-level code
bash run_project.sh

```

#### 📋 Usage Examples

##### 1. Portfolio Website
```bash
python main.py --mode project \
    --project_type web_visualization \
    --requirement "Create a personal portfolio with project showcase and contact form" \
    --output_dir "my_portfolio"
```

##### 2. Interactive Dashboard
```bash
python main.py --mode project \
    --project_type web_visualization \
    --requirement "Create a sales analytics dashboard with charts, filters, and real-time updates" \
    --output_dir "sales_dashboard"
```

##### 3. Data Visualization App
```bash
python main.py --mode project \
    --project_type web_visualization \
    --requirement "Create an interactive data explorer with multiple chart types" \
    --output_dir "data_explorer"
```

### Citation
```
@article{Self-collaboration,
  author={Dong, Yihong and Jiang, Xue and Jin, Zhi and Li, Ge},
  title        = {Self-collaboration Code Generation via ChatGPT},
  journal      = {{ACM} Trans. Softw. Eng. Methodol.},
  volume       = {33},
  number       = {7},
  pages        = {189:1--189:38},
  year         = {2024}
  keywords     = {Code generation, large language models, multi-agent collaboration, software development, software engineering}
}
```
