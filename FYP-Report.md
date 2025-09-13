![A close up of a logo Description automatically
generated](media/image1.png){width="5.5419510061242345in"
height="0.902823709536308in"}

FINAL YEAR PROJECT INTERIM REPORT

FYP01-DS-T2510-0038

Stock Market Sentiment Dashboard: Analysis and Insights

241UC240L7

BAIDAQ ABDULRAHMAN

BACHELOR OF COMPUTER SCIENCE B.CS (HONS) DATA SCIENCE

JULY 2025

> 
>
> FYP01-DS-T2510-0038
>
> Stock Market Sentiment Dashboard: Analysis and Insights

1.  

BY

BAIDAQ ABDULRAHMAN

241UC240L7

PROJECT INTERIM REPORT SUBMITTED IN PARTIAL FULFILMENT OF THE

REQUIREMENT FOR THE DEGREE OF

BACHELOR OF COMPUTER SCIENCE B.CS (HONS) DATA SCIENCE

in the

Faculty of Computing and Informatics

MULTIMEDIA UNIVERSITY

MALAYSIA

JULY 2025

# Abstract

This report presents the development of the Stock Market Sentiment
Dashboard: Analysis and Insights, an open-source, web-based platform
crafted to deliver accessible, sentiment-driven financial analytics for
retail investors, financial analysts, and researchers. The project
tackles the barriers posed by expensive commercial sentiment analysis
tools and the shortcomings of existing open-source alternatives,
leveraging free-tier APIs and innovative Natural Language Processing
(NLP) techniques to provide a cost-effective solution.

The document outlines the problem statement, objectives, and scope,
supported by a thorough literature review that explores behavioral
finance, advanced NLP methodologies, and the relationship between public
sentiment and stock price dynamics. The system aggregates unstructured
textual data from financial news sources (via FinHub, Marketaux, and
NewsAPI) and social media discussions (Reddit via PRAW) for technology
stocks, including the top 20 IXT stocks and the Magnificent Seven.

By employing FinBERT for financial news and VADER for Reddit posts, the
dashboard classifies sentiment as positive, negative, or neutral, and
offers interactive visualizations juxtaposed with historical stock
prices from Yahoo Finance. A dynamic correlation module computes Pearson
coefficients to reveal insights into the interplay between sentiment
scores and price movements across user-selectable timeframes (1, 7, and
14 days).

The requirements analysis delineates both functional and non-functional
system needs, while the design phase adopts a layered architecture to
ensure modularity, scalability, and ease of maintenance, reinforced by
detailed class diagrams, sequence diagrams, and an entity-relationship
model. The prototype section illustrates user-friendly interfaces for
sentiment analysis, correlation insights, and administrative system
management.

The implementation plan organizes development into a structured 14-week
timeline, encompassing phases from data pipeline construction to
rigorous testing and deployment. Delivered with a fully documented,
GitHub-hosted codebase, this system bridges the gap between qualitative
market psychology and quantitative financial data, empowering users with
a reproducible, intuitive tool to explore sentiment-driven market
insights.

# Table of Contents

#  {#section .TOC-Heading}

[Copyright [iv](#_Toc202458249)](#_Toc202458249)

[Declaration [v](#_Toc202458250)](#_Toc202458250)

[Acknowledgements [vi](#_Toc202458251)](#_Toc202458251)

[Abstract [vii](#abstract)](#abstract)

[Table of Contents [viii](#table-of-contents)](#table-of-contents)

[List of Tables [xi](#list-of-tables)](#list-of-tables)

[List of Figures [xii](#list-of-figures)](#list-of-figures)

[List of Appendices [xiv](#list-of-appendices)](#list-of-appendices)

[Chapter 1: Introduction
[1](#chapter-1-introduction)](#chapter-1-introduction)

[1.1 Overview [1](#overview)](#overview)

[1.2 Problem Statement [2](#problem-statement)](#problem-statement)

[1.3 Objectives [2](#objectives)](#objectives)

[1.4 Outcomes [3](#outcomes)](#outcomes)

[1.5 Project Scope [4](#project-scope)](#project-scope)

[1.6 Gantt Chart [5](#gantt-chart)](#gantt-chart)

[Chapter 2: Literature Review
[6](#chapter-2-literature-review)](#chapter-2-literature-review)

[2.1 Overview [6](#overview-1)](#overview-1)

[2.2 Behavioral Finance and Market Psychology
[6](#behavioral-finance-and-market-psychology)](#behavioral-finance-and-market-psychology)

[2.3 Sentiment Analysis in Financial Markets
[7](#sentiment-analysis-in-financial-markets)](#sentiment-analysis-in-financial-markets)

[2.3.1 Methodologies in Financial Sentiment Analysis
[8](#methodologies-in-financial-sentiment-analysis)](#methodologies-in-financial-sentiment-analysis)

[2.3.2 Applications and Predictive Power
[8](#applications-and-predictive-power)](#applications-and-predictive-power)

[2.3.3 Model Selection Rationale
[9](#model-selection-rationale)](#model-selection-rationale)

[2.3.4 Model Justification & Evaluation Results
[10](#model-justification-evaluation-results)](#model-justification-evaluation-results)

[2.3.5 Enhancing VADER's Performance
[12](#enhancing-vaders-performance)](#enhancing-vaders-performance)

[2.3.6 Challenges and Considerations
[12](#challenges-and-considerations)](#challenges-and-considerations)

[2.4 Existing Sentiment Analysis Tools and Platforms
[13](#existing-sentiment-analysis-tools-and-platforms)](#existing-sentiment-analysis-tools-and-platforms)

[2.4.1 Commercial Platforms
[13](#commercial-platforms)](#commercial-platforms)

[2.4.2 Academic and Open-Source Tools
[14](#academic-and-open-source-tools)](#academic-and-open-source-tools)

[2.4.3 Limitations and Challenges
[14](#limitations-and-challenges)](#limitations-and-challenges)

[2.4.4 Emerging Trends [15](#emerging-trends)](#emerging-trends)

[2.5 Role of APIs and Data Sources in Sentiment Analysis
[15](#role-of-apis-and-data-sources-in-sentiment-analysis)](#role-of-apis-and-data-sources-in-sentiment-analysis)

[2.5.1 Utilization of Free APIs
[15](#utilization-of-free-apis)](#utilization-of-free-apis)

[2.5.2 Challenges in Using Free APIs
[16](#challenges-in-using-free-apis)](#challenges-in-using-free-apis)

[2.5.3 Ethical Considerations
[17](#ethical-considerations)](#ethical-considerations)

[2.6 Correlation Between Sentiment and Stock Prices
[17](#correlation-between-sentiment-and-stock-prices)](#correlation-between-sentiment-and-stock-prices)

[2.6.1 Empirical Evidence of Correlation
[17](#empirical-evidence-of-correlation)](#empirical-evidence-of-correlation)

[2.6.2 Statistical Methods Utilized
[18](#statistical-methods-utilized)](#statistical-methods-utilized)

[2.6.3 Conflicting Findings and Limitations
[18](#conflicting-findings-and-limitations)](#conflicting-findings-and-limitations)

[2.7 Gaps in Current Research
[19](#gaps-in-current-research)](#gaps-in-current-research)

[2.8 Summary [20](#summary)](#summary)

[Chapter 3: Theoretical Framework
[22](#chapter-3-theoretical-framework)](#chapter-3-theoretical-framework)

[3.1 Overview [22](#overview-2)](#overview-2)

[3.2 Justification of Tools and Libraries
[22](#justification-of-tools-and-libraries)](#justification-of-tools-and-libraries)

[3.3 Data Acquisition and API Configuration
[24](#data-acquisition-and-api-configuration)](#data-acquisition-and-api-configuration)

[3.3.1 Principles of API Access
[24](#principles-of-api-access)](#principles-of-api-access)

[3.3.2 API Service Configuration
[24](#api-service-configuration)](#api-service-configuration)

[3.4 Setup and Imports [26](#setup-and-imports)](#setup-and-imports)

[3.5 Define Stocks and Time Period
[28](#define-stocks-and-time-period)](#define-stocks-and-time-period)

[3.6 Data Collection [29](#data-collection)](#data-collection)

[3.6.1 Reddit Data Collection with PRAW
[30](#reddit-data-collection-with-praw)](#reddit-data-collection-with-praw)

[3.6.2 Finnhub News Collection
[32](#finnhub-news-collection)](#finnhub-news-collection)

[3.6.3 Marketaux News Collection
[33](#marketaux-news-collection)](#marketaux-news-collection)

[3.6.4 NewsAPI Data Collection
[35](#newsapi-data-collection)](#newsapi-data-collection)

[3.7 Text Preprocessing [37](#text-preprocessing)](#text-preprocessing)

[3.7.1 Preprocessing for FinBERT (Finnhub, Marketaux, NewsAPI)
[37](#preprocessing-for-finbert-finnhub-marketaux-newsapi)](#preprocessing-for-finbert-finnhub-marketaux-newsapi)

[3.7.2 Preprocessing for VADER (Reddit)
[38](#preprocessing-for-vader-reddit)](#preprocessing-for-vader-reddit)

[3.8 Sentiment Analysis [39](#sentiment-analysis)](#sentiment-analysis)

[3.8.1 FinBERT Sentiment Analysis
[40](#finbert-sentiment-analysis)](#finbert-sentiment-analysis)

[3.8.1.1 FinBERT Mathematical Foundations
[40](#finbert-mathematical-foundations)](#finbert-mathematical-foundations)

[3.8.2 VADER Sentiment Analysis
[44](#vader-sentiment-analysis)](#vader-sentiment-analysis)

[3.8.3 FinBERT Sentiment Analysis Evaluation
[45](#finbert-sentiment-analysis-evaluation)](#finbert-sentiment-analysis-evaluation)

[3.8.4 VADER Sentiment Analysis Evaluation
[49](#vader-sentiment-analysis-evaluation)](#vader-sentiment-analysis-evaluation)

[3.9 Aggregation [52](#aggregation)](#aggregation)

[3.10 Fetch Stock Prices [53](#fetch-stock-prices)](#fetch-stock-prices)

[3.11 Visualization [54](#visualization)](#visualization)

[3.12 Pipeline Challenges and Mitigation Strategies
[56](#pipeline-challenges-and-mitigation-strategies)](#pipeline-challenges-and-mitigation-strategies)

[Chapter 4: Requirements
[57](#chapter-4-requirements)](#chapter-4-requirements)

[4.1 Overview [57](#overview-3)](#overview-3)

[4.1.1 Why We Need Functional Requirements
[57](#why-we-need-functional-requirements)](#why-we-need-functional-requirements)

[4.2 Functional Requirements
[58](#functional-requirements)](#functional-requirements)

[4.2.1 User Functional Requirements
[58](#user-functional-requirements)](#user-functional-requirements)

[4.2.2 System Functional Requirements
[59](#system-functional-requirements)](#system-functional-requirements)

[Chapter 5: Analysis [61](#chapter-5-analysis)](#chapter-5-analysis)

[5.1 Overview [61](#overview-4)](#overview-4)

[5.2 Use-Case Modeling [61](#use-case-modeling)](#use-case-modeling)

[5.2.1 Use-Case Diagram [62](#use-case-diagram)](#use-case-diagram)

[5.3 Use-Case Descriptions
[62](#use-case-descriptions)](#use-case-descriptions)

[5.3.1 User Use-Case Descriptions
[63](#user-use-case-descriptions)](#user-use-case-descriptions)

[5.3.2 System Use-Case Descriptions
[69](#system-use-case-descriptions)](#system-use-case-descriptions)

[5.4 Dynamic Model [75](#dynamic-model)](#dynamic-model)

[5.4.1 Activity Diagram [75](#activity-diagram)](#activity-diagram)

[5.5 State Diagrams [80](#state-diagrams)](#state-diagrams)

[5.6 Sequence Diagram [83](#sequence-diagram)](#sequence-diagram)

[5.7 Object Model Diagram
[103](#a-diagram-of-a-network-ai-generated-content-may-be-incorrect.5.7-object-model-diagram)](#a-diagram-of-a-network-ai-generated-content-may-be-incorrect.5.7-object-model-diagram)

[5.8 ER diagram [104](#er-diagram)](#er-diagram)

[5.9 Data dictionaries [105](#data-dictionaries)](#data-dictionaries)

[Chapter 6: Design [107](#chapter-6-design)](#chapter-6-design)

[6.1 Introduction [107](#introduction)](#introduction)

[6.2 Overview of Software Architectures
[108](#overview-of-software-architectures)](#overview-of-software-architectures)

[6.2.1 Architecture Option 1: Event-Driven Architecture
[108](#architecture-option-1-event-driven-architecture)](#architecture-option-1-event-driven-architecture)

[6.2.2 Architecture Option 2: Microservices Architecture
[110](#architecture-option-2-microservices-architecture)](#architecture-option-2-microservices-architecture)

[6.2.3 Architecture Option 3: Layered Architecture
[111](#architecture-option-3-layered-architecture)](#architecture-option-3-layered-architecture)

[6.3 Selected Software Architecture
[113](#selected-software-architecture)](#selected-software-architecture)

[6.4 Design Model [116](#design-model)](#design-model)

[6.5 Deployment [119](#deployment)](#deployment)

[6.5.1 Deployment Architecture Overview
[119](#deployment-architecture-overview)](#deployment-architecture-overview)

[6.5.2 Component Deployment Breakdown
[119](#component-deployment-breakdown)](#component-deployment-breakdown)

[6.5.3 Deployment Relationships and Runtime Interaction
[120](#deployment-relationships-and-runtime-interaction)](#deployment-relationships-and-runtime-interaction)

[6.6 Prototype [123](#prototype)](#prototype)

[6.7 Conclusion [131](#conclusion)](#conclusion)

[Chapter 7: Implementation Plan
[132](#chapter-7-implementation-plan)](#chapter-7-implementation-plan)

[7.1 Introduction [132](#introduction-1)](#introduction-1)

[7.2 Implementation Plan Phases
[132](#implementation-plan-phases)](#implementation-plan-phases)

[References [135](#references)](#references)

[Appendix A: Meeting Logs [138](#_Toc202458353)](#_Toc202458353)

[Appendix B: Turnitin Similarity Index Page
[174](#_Toc202458354)](#_Toc202458354)

# List of Tables

[Table 4.1: User Functional Requirements
[58](#_z4fgvob2eotf)](#_z4fgvob2eotf)

[Table 4.2: System Functional Requirements
[59](#_Toc199184011)](#_Toc199184011)

[Table 4.3: Non-Functional Requirements
[60](#_Toc201534930)](#_Toc201534930)

[Table 5.1: Use-Case for Viewing the Sentiment Dashboard
[63](#_Toc201534931)](#_Toc201534931)

[Table 5.2: Use-Case for Selecting a Time Range
[63](#_Toc201534932)](#_Toc201534932)

[Table 5.3: Use-Case for Filtering by Stock
[64](#_Toc201534933)](#_Toc201534933)

[Table 5.4: Use-Case for Comparing Sentiment vs. Stock Price
[65](#_Toc201534934)](#_Toc201534934)

[Table 5.5: Use-Case for Viewing Dynamic Correlation Analysis
[65](#_Toc201534935)](#_Toc201534935)

[Table 5.6: Use-Case for Evaluating Model Accuracy
[66](#_Toc201534936)](#_Toc201534936)

[Table 5.7: Use-Case for Configuring API Keys
[67](#_Toc199184028)](#_Toc199184028)

[Table 5.8: Use-Case for Updating the Stock Watchlist
[67](#_Toc201534938)](#_Toc201534938)

[Table 5.9: Use-Case for Managing Data Storage Settings
[68](#_Toc199184032)](#_Toc199184032)

[Table 5.10: Use-Case for Viewing System Logs
[69](#_Toc201534940)](#_Toc201534940)

[Table 5.11: Use-Case for Running the Data Collection Pipeline
[69](#_Toc201534941)](#_Toc201534941)

[Table 5.12: Use-Case for Preprocessing Raw Data
[70](#_Toc199184038)](#_Toc199184038)

[Table 5.13: Use-Case for Performing Sentiment Analysis
[71](#_Toc201534943)](#_Toc201534943)

[Table 5.14: Use-Case for Storing Sentiment Results
[71](#_Toc199184042)](#_Toc199184042)

[Table 5.15: Use-Case for Scheduling Batch Data Fetching
[72](#_Toc201534945)](#_Toc201534945)

[Table 5.16: Use-Case for Handling API Rate Limits
[72](#_Toc201534946)](#_Toc201534946)

[Table 5.17: Use-Case for Normalizing Timestamps
[73](#_Toc201534947)](#_Toc201534947)

[Table 5.18: Use-Case for Triggering Visualization Updates
[74](#_Toc201534948)](#_Toc201534948)

[Table 5.19: Use-Case for Logging Pipeline Operations
[74](#_Toc201534949)](#_Toc201534949)

[Table 5.20: Stock Data Dictionary
[105](#_Toc201534950)](#_Toc201534950)

[Table 5.21: SentimentRecord Data Dictionary
[105](#_Toc201534951)](#_Toc201534951)

[Table 5.22: JobLog Data Dictionary
[106](#_Toc201534952)](#_Toc201534952)

[Table 5.23: CorrelationResult Data Dictionary
[106](#_Toc201534953)](#_Toc201534953)

[Table 5.24: ModelEvaluationResult Data Dictionary
[106](#_Toc201534954)](#_Toc201534954)

# List of Figures

[Figure 1.1: Gantt Chart for FYP1 [5](#_Toc199094322)](#_Toc199094322)

[Figure 2.1: FinBERT model evaluation
[10](#_Toc201534996)](#_Toc201534996)

[Figure 2.2: VADER model evaluation
[11](#_Toc201534997)](#_Toc201534997)

[Figure 5.1: Use-Case Diagram for the Stock Market Sentiment Dashboard
[62](#_Toc201534998)](#_Toc201534998)

[Figure 5.2: User Dashboard Interaction Diagram
[75](#_Toc199184358)](#_Toc199184358)

[Figure 5.3: Data Collection Activity Diagram
[76](#_Toc199184353)](#_Toc199184353)

[Figure 5.4: Preprocessing Activity Diagram
[77](#_Toc199184354)](#_Toc199184354)

[Figure 5.5: Sentiment Analysis Activity Diagram
[78](#_Toc199184355)](#_Toc199184355)

[Figure 5.6: Storage Module Activity Diagram
[79](#_Toc199184356)](#_Toc199184356)

[Figure 5.7: Data Collection State Diagram
[80](#_Toc199184359)](#_Toc199184359)

[Figure 5.8: Sentiment Record State Diagram
[81](#_Toc201535005)](#_Toc201535005)

[Figure 5.9: Pipeline State Diagram
[82](#_Toc201535006)](#_Toc201535006)

[Figure 5.10: View Sentiment Dashboard Sequence Diagram
[83](#_Toc199184366)](#_Toc199184366)

[Figure 5.11: Select Time Range Sequence Diagram
[84](#_Toc199184367)](#_Toc199184367)

[Figure 5.12: Filter by Stock Sequence Diagram
[85](#_Toc199184368)](#_Toc199184368)

[Figure 5.13: Compare Sentiment vs. Stock Price Sequence Diagram
[86](#_Toc199184369)](#_Toc199184369)

[Figure 5.14: View Dynamic Correlation Analysis Sequence Diagram
[87](#_Toc199184370)](#_Toc199184370)

[Figure 5.15: Evaluate Model Accuracy Sequence Diagram
[88](#_Toc199184371)](#_Toc199184371)

[Figure 5.16: Configure API Keys Sequence Diagram
[89](#_Toc199184372)](#_Toc199184372)

[Figure 5.17: Update Stock Watchlist Sequence Diagram
[90](#_Toc199184373)](#_Toc199184373)

[Figure 5.18: Manage Data Storage Sequence Diagram
[91](#_Toc199184374)](#_Toc199184374)

[Figure 5.19: View System Logs Sequence Diagram
[92](#_Toc199184375)](#_Toc199184375)

[Figure 5.20: Data Collection Pipeline Sequence Diagram
[93](#_Toc199184376)](#_Toc199184376)

[Figure 5.21: Preprocess Raw Data Sequence Diagram
[94](#_Toc199184377)](#_Toc199184377)

[Figure 5.22: Perform Sentiment Analysis Sequence Diagram
[95](#_Toc199184378)](#_Toc199184378)

[Figure 5.23: Store Sentiment Results Sequence Diagram
[96](#_Toc199184379)](#_Toc199184379)

[Figure 5.24: Schedule Batch Data Fetching Sequence Diagram
[97](#_Toc199184380)](#_Toc199184380)

[Figure 5.25: Handle API Rate Limits Sequence Diagram
[98](#_Toc199184381)](#_Toc199184381)

[Figure 5.26: Normalize Timestamps Sequence Diagram
[99](#_Toc199184382)](#_Toc199184382)

[Figure 5.27: Trigger Visualization Updates Sequence Diagram
[100](#_Toc199184383)](#_Toc199184383)

[Figure 5.28: Log Pipeline Operations Sequence Diagram
[101](#_Toc199184384)](#_Toc199184384)

[Figure 5.29: Class Diagram [103](#_Toc201535026)](#_Toc201535026)

[Figure 5.30: ER Diagram [104](#_Toc201535027)](#_Toc201535027)

[Figure 6.1: Layered Architecture Diagram
[113](#_Toc201535033)](#_Toc201535033)

[Figure 6.2: Refined Class Diagram with Packages and Design Patterns
[116](#_Toc201535034)](#_Toc201535034)

[Figure 6.3 Deployment Diagram [122](#_Toc201535035)](#_Toc201535035)

[Figure 6.4: Dashboard Page [123](#_Toc201535028)](#_Toc201535028)

[Figure 6.5: Stock Analysis Page [124](#_Toc201535029)](#_Toc201535029)

[Figure 6.6: Sentiment vs Price Page
[125](#_Toc201535030)](#_Toc201535030)

[Figure 6.7: Correlation Analysis Page
[126](#_Toc201535031)](#_Toc201535031)

[Figure 6.8: Sentiment Trends Page
[127](#_Toc201535032)](#_Toc201535032)

[Figure 6.9: Admin Dashboard Page [128](#_Toc201802316)](#_Toc201802316)

[Figure 6.10: Model Accuracy Page [128](#_Toc201802317)](#_Toc201802317)

[Figure 6.11: API Configuration Page
[129](#_Toc201802318)](#_Toc201802318)

[Figure 6.12: Watchlist Manager Page
[129](#_Toc201802319)](#_Toc201802319)

[Figure 6.13: Storage Settings Page
[130](#_Toc201802320)](#_Toc201802320)

[Figure 6.14: System Logs Page [131](#_Toc201802321)](#_Toc201802321)

[Figure 7.1 Implementation Plan Gantt chart
[132](#_Toc201535036)](#_Toc201535036)

# 

# List of Appendices

[Appendix A: Meeting Logs [138](#_Toc202458353)](#_Toc202458353)

[Appendix B: Turnitin Similarity Index Page
[174](#_Toc202458354)](#_Toc202458354)

# Chapter 1: Introduction

## 1.1 Overview

The advent of digital sites has changed financial markets; social media,
news, and online forums are influencing the mood of the people and
determining stock market behaviour. Social media sites such as
r/wallstreetbets on reddit have proven capable of causing market
conditions that breed volatility as in the 2021 GameStop short squeeze
when the collective opinion of investors prevailed over conventional
valuation. Such a shift criticises the Efficient Market Hypothesis
(EMH), which presupposes rational markets, and highlights the need to
consider the influence of behavioural finance and its implications in
emotional market behaviours such as fear, greed and excitement.

A viable solution to measure these qualitative signals on unstructured
text is sentiment analysis that is fuelled by Natural Language
Processing (NLP). Sentiment analysis can reveal the psychology of the
markets by examining sources, including social media posts, financial
news, and investor discussion and improve predictive models.

Its potentialities are pictured in recent studies:

- Chen et al. (2025) evidence that hybrid sentiment models enhance
  increment in stock trend predictions when combined with history stock
  trends information and Liu et al. (2025) provide solutions on
  multi-level sentiment frameworks with Large Language Models (LLMs) to
  be used in real-time trends in the market.

Although promising, it is not uncommon to encounter obstacles to the use
of current sentiment tools: cost, processing lag or connection with
financial data. To fill this gap, the Stock Market Sentiment Dashboard:
Analysis and Insights project will create an open-source that is
scalable project. It aggregates and analyses sentiment data of a
hand-picked set of top technology equities, displaying interactive
analyses to make complicated financial analytics seeable to all.

## 1.2 Problem Statement

Financial markets are increasingly driven by public sentiment,
challenging the EMH\'s assumption of rationality. Behavioral finance
reveals how emotions optimism, fear, or hype can cause price anomalies,
as evidenced by events like the GameStop surge. However, traditional
financial tools, focused on quantitative metrics like price trends and
financial ratios, often fail to capture these qualitative influences.

Current sentiment analysis solutions have limitations: commercial
platforms are expensive, require proprietary data, and are limited to
certain investors, making them inaccessible to many users especially
retail investors. Open-source alternatives, while cost-effective, often
struggle with noisy data from social media and news or lack
sophisticated integration with financial indicators.

This project addresses the following issues:

- Limited integration of sentiment data with stock price trends in
  accessible tools.

- Lack of cost-effective, near real-time sentiment analysis platforms
  for non-institutional investors.

- Challenges in processing noisy, unstructured data from diverse
  sources.

- Absence of platforms that allow users to dynamically visualize and
  analyze sentiment-price relationships.

By developing a dashboard that leverages free APIs, specialized NLP
models (FinBERT, VADER), and open-source visualization tools, this
project aims to provide an affordable, modular solution for retail
traders, financial analysts, and academic researchers to explore
sentiment-driven market insights.

## 1.3 Objectives

The primary goal of this project is to design, develop, and deliver a
comprehensive sentiment analysis dashboard for the stock market. The key
objectives are:

- To develop a scalable data collection pipeline that automatically
  extracts relevant financial news and social media discussions from
  multiple free APIs, including Reddit, FinHub, Marketaux, and NewsAPI,
  for a curated list of leading technology stocks (including the top 20
  IXT stocks and the Magnificent Seven combined).

- To implement and integrate two specialized Natural Language Processing
  models using FinBERT for financial news and VADER for social media
  texts to accurately classify the sentiment of the collected data as
  positive, negative, or neutral.

- To design and build a user-friendly, interactive web dashboard using a
  modern framework or any other platform. The dashboard will visualize
  sentiment trends alongside historical stock prices, offering
  selectable 1-day, 7-day, and 14-day analysis periods.

- To embed a dynamic analysis module within the dashboard that allows
  users to compute and visualize the Pearson correlation between
  sentiment scores and stock price movements for any selected stock and
  timeframe.

- To deliver the entire project as a reproducible, open-source
  prototype, complete with a documented codebase, a user guide, and
  deployment instructions hosted on GitHub.

## 1.4 Outcomes

The project will deliver the following tangible outcomes:

1.  **Functional and Analytical Dashboard Prototype:** A web-based
    dashboard featuring interactive visualizations for a curated list of
    leading technology stocks. The dashboard will allow users to compare
    sentiment and stock prices across multiple timeframes (1, 7, and 14
    days) and will include a dynamic correlation analysis feature to
    provide instant quantitative insights.

2.  **End-to-End Sentiment Pipeline:** A scalable pipeline that fetches
    data from Reddit, FinHub, Marketaux, and NewsAPI, preprocesses it,
    applies FinBERT and VADER for sentiment classification, and
    populates a data store ready for the dashboard.

3.  **Open-Source Codebase:** A GitHub repository with the full
    codebase, including setup instructions, a README, and a user manual
    to ensure reproducibility and community use.

4.  **Knowledge Enhancement:** Applied learning in NLP, financial
    analytics, data engineering, and interactive web visualization,
    strengthening expertise in building end-to-end data science
    applications.

## 1.5 Project Scope

The project focuses on sentiment analysis for stock market insights,
emphasizing accessibility and reproducibility. Its scope is defined as
follows:

**Inclusions**

- **Data Sources:** Public data from Reddit (via PRAW), FinHub,
  Marketaux, and NewsAPI, focusing on English-language texts related to
  the top 20 IXT stocks and the Magnificent Seven combined.

- **Sentiment Classification:** FinBERT for financial news and VADER for
  Reddit posts, classifying sentiment as positive, negative, or neutral.

- **Financial Data:** Historical stock prices from Yahoo Finance
  (via yfinance) for correlation analysis.

- **Visualization:** An interactive dashboard built with a modern
  framework, featuring dual-axis time-series plots and dynamic
  correlation tables.

- **Deployment:** Open-source codebase on GitHub with full documentation
  for academic and community use.

**Limitations**

- **Data Restrictions:** To ensure the project is open and reproducible,
  it will exclusively leverage publicly available data and free-tier
  APIs, intentionally avoiding proprietary datasets or paid services.

- **Prediction Scope:** The project focuses on correlation analysis to
  uncover relationships, not on building a model for precise stock price
  prediction or generating trading recommendations.

- **Real-Time Constraints:** The system will rely on daily batch
  processing for updates due to API rate limits, not second-by-second
  streaming.

- **User Features:** The dashboard will not include user authentication
  or personalized portfolio tracking, prioritizing general-purpose
  analysis.

## 1.6 Gantt Chart

![[]{#_Toc199094322 .anchor}Figure 1.1: Gantt Chart for
FYP1](media/image2.png){width="4.904166666666667in"
height="3.265980971128609in"}

# Chapter 2: Literature Review

## 2.1 Overview

The expansive increase in user-generated content on the digital
platforms has completely changed the way the financial markets work. The
use of social media, online news, and investor forums has become a vital
aspect of driving the public opinion, which has never been witnessed in
regard to influencing stock market behaviour. To put it bluntly,
traditional financial analysis is based on numeric data and is
structured to lay heavy emphasis on the quantitative aspects of the
market psychology. Improved sentiment analysis like Natural Language
Processing (NLP) technique gave mainstream researchers the possibility
to gather and measure interesting information about unstructured text
providing insight into the market positioning fuelled by affects and
emotions.

The chapter is a critical review of the literature available on
sentiment analysis in the context of financial markets, and it is based
on the premises of behavioural finance. It takes a critical look at
existing methodologies, tools and data sources used in doing
sentiment-driven analysis, and outlines capabilities and inabilities of
existing solutions. Reflectively, this chapter not only lays down the
scholarly and literal ground upon which the proposed **Stock Market
Sentiment Dashboard** as an open source and near real-time system
emerges but also exhaustively reveals the loopholes in the present
research scene that the proposed system is proposed to fill.

## 2.2 Behavioral Finance and Market Psychology

Standard financial theories, in particular Efficient Market Hypothesis
(EMH) assume that financial markets are rational and informationally
efficient, which means that prices of assets reflect all available
information. However, real life experiences often indicate that there
are behaviours that do not match to this standard and hence the need to
seek alternative explanations that are based on behavioural finance.
This sub-discipline examines how much cognitive biases and affective
states influence financial decisions.

Probably the most significant addition to the behavioural finance
literature is the Prospect Theory, which was initially proposed by
Daniel Kahneman and Amos Tversky in 1979. This framework challenges the
conventional utility-based frameworks by illustrating the systematic
risk valuation asymmetries. In particular, the Prospect Theory assumes a
loss aversion: people place a higher stress on losses than on the equal
gains, which distorts risk-taking behaviour.

Such emotional factors as fear, greed, and herd mentality also have a
powerful impact on the dynamics of stock prices. An example is the
GameStop short squeeze of 2021, whereby retail investors, organizing
themselves in online forums such as the subreddit r/wallstreetbets and
Twitter, collectively purchased GameStop shares, causing a sharp rise in
the share price and huge losses to hedge funds with short positions.
This episode shows the ability of collective feeling to upset the
traditional market equilibria.

The application of behavioural finance knowledge to the task of market
evaluation has led to the development of sentiment analysis, a process
of measuring the views expressed in the media (including news stories,
social media, and financial reports). In empirical studies, the
sentiment indicators have been shown to increase the predictive power,
with sharp mood swings tending to precede market change. To give an
example, recent research indicates that there is a very positive
relationship between positive news sentiment and positive price trend
and a reciprocating negative relationship between negative prices
pressure.

The acknowledgment of the role of the behavioural finance allows
financial analysts and investors to explain with more accuracy the
psychological mechanisms of the market anomalies. By combining sentiment
analysis and the established financial models, the explanatory power of
the latter is extended as they are placed into a larger context, where
the quantitative information is connected to the qualitative aspect of
investor behaviour.

## 2.3 Sentiment Analysis in Financial Markets

The proliferation of digital platforms has transformed the landscape of
financial markets, making investor sentiment a pivotal factor in market
dynamics. Social media, news outlets, and online forums have become rich
sources of unstructured data reflecting public opinion and emotional
responses to market events. Sentiment analysis, leveraging Natural
Language Processing (NLP) techniques, has emerged as a critical tool for
extracting and quantifying these sentiments to inform trading strategies
and market predictions.

### 2.3.1 Methodologies in Financial Sentiment Analysis

Recent advancements have seen the integration of sophisticated models to
enhance sentiment analysis accuracy:

- **Lexicon-Based Approaches**: Utilize predefined dictionaries to
  classify sentiment. While straightforward, they often lack context
  sensitivity.

- **Machine Learning Models**: Algorithms like Support Vector Machines
  (SVM) and Random Forests trained on labelled datasets to predict
  sentiment.

- **Deep Learning Techniques**: Models such as Long Short-Term Memory
  (LSTM) networks and Transformers capture complex patterns in textual
  data.

- **Large Language Models (LLMs)**: The deployment of LLMs, including
  FinBERT and GPT-based models, has significantly improved the
  contextual understanding of financial texts, leading to more nuanced
  sentiment analysis. Recent studies highlight the effectiveness of
  these models in capturing the intricacies of financial language and
  sentiment.

### 2.3.2 Applications and Predictive Power

The empirical studies support the foretelling abilities of sentiment
analysis for financial settings:

- A comprehensive bibliometric review of 223 articles published between
  2010 and 2022 shows that hybrid models, a mixture of lexicon-based and
  deep learning models, have a healthy performance in the extraction of
  investor sentiment, which is also an important element of determining
  the trend in the stock market.

- Sentiment analysis has been demonstrated to complement in predictions
  of the stock price movements after incorporation into financial
  models, especially where the data provided by the social media
  platforms are used as the source of inputs. These websites offer
  real-time information on the mood and response of investors as far as
  market actions are concerned. As an example, **research** published in
  2023 by Deng et al. investigated the application of LLMs in the
  analysis of the sentiment on Reddit markets using a semi-supervised
  method to assign a label of sentiment to the posts made on Reddit. The
  research has established that with the application of Chain-of-Thought
  reasoning on LLMs, a stable sentiment label was adopted, and a level
  of performance equal to supervised models was attained, and the
  accuracy of the final model performed competitively in predicting
  financial sentiment trends. This underscores the possibilities that
  LLMs have in improving sentiment analysis on such platforms as Reddit,
  which is why the project uses VADER to do the same with related data.

- The use of LLMs in the financial sector has led to the creation of
  more advanced sentiment analysis tools, which have the ability to
  assess the finances in the light of subtlety and complexity of the
  language. Such a breakthrough has resulted in better market forecasts
  and trading habits.

### 2.3.3 Model Selection Rationale

To achieve the objective of the project, which is analysing sentiment on
curated list of top technology stocks, two sentiment analysis models,
namely FinBERT and VADER were selected as they have complementary
capabilities in working with financial news and social media data
respectively.

- **FinBERT**: Another transformer model, FinBERT by ProsusAI, is
  specifically fine-tuned on financial text, which makes it suitable
  when analysing news articles provided by FinHub, Marketaux, NewsAPI.
  Its domain expertise results in a high accuracy of sentiment
  (positive, negative, neutral) classification in relation to financial
  usage with appropriate identification of subtle language and jargon
  that are common within funding matters. The high performance as shown
  in other studies (Kirtac & Germano, 2025) justifies the choice of
  FinBERT to carry out reliable sentiment extraction on structured
  financial news.

- **VADER**: The Valence Aware Dictionary and sentiment reasoner is a
  rule-based model that is optimized to social media texts that was
  chosen to analyse the Reddit posts using PRAW. VADER is light weighted
  and supports both informal language, slangs, and emoticons, which
  makes it applicable in noisy and unstructured datasets like Reddit.
  Although more simplistic than transformer models, the computational
  efficiency and usability of VADER fit within the scope of the project
  of developing an open-source, resource-friendly dashboard that allows
  resource-limited retail investors to make more informed decisions.

### 2.3.4 Model Justification & Evaluation Results

Both models were evaluated on labelled ground truth datasets to assess
their performance and validate their suitability for the project.

![[]{#_Toc201534996 .anchor}Figure 2.1: FinBERT model
evaluation](media/image3.png){width="3.2in"
height="3.4992082239720035in"}

**FinBERT Evaluation**: FinBERT was evaluated on a dataset of 2,264
financial sentences (1,391 neutral, 570 positives, 303 negative). The
model achieved:

- **Accuracy**: 97.17%

- **Precision**: 95.85%

- **Recall**: 97.59%

- **F1-Score**: 96.25%

**Class Insights**:

- **Negative**: Precision 0.91, Recall 0.98, F1 0.94, excellent recall
  ensures most negatives are identified.

- **Neutral**: Precision 1.00, Recall 0.97, F1 0.98, perfect precision,
  no misclassifications as neutral.

- **Positive**: Precision 0.95, Recall 0.98, F1 0.96, strong performance
  across metrics. FinBERT's high accuracy and balanced performance
  across classes confirm its reliability for financial news sentiment
  analysis, supporting its role in generating precise inputs for stock
  sentiment trends.

<figure>
<img src="media/image4.png" style="width:3.7875in;height:3.56074in"
alt="A screenshot of a computer AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201534997" class="anchor"></span>Figure
2.2: VADER model evaluation</p></figcaption>
</figure>

**VADER Evaluation**: VADER was assessed on a synthetic dataset of 1,000
Reddit comments, manually labelled as positive, neutral, or negative.
The model achieved:

- **Accuracy**: 59.6%

- **Precision**: 67.57%

- **Recall**: 60.19%

- **F1-Score**: 59.39%

**Class Insights**:

- **Negative**: Precision 0.56, Recall 0.49, F1 0.52, balanced
  misclassifications between negative and neutral.

- **Neutral**: Precision 0.47, Recall 0.82, F1 0.60, high recall but low
  precision, indicating overclassification as neutral.

- **Positive**: Precision 1.00, Recall 0.49, F1 0.66, perfect precision
  but low recall, missing many positives. VADER's performance, while
  lower than FinBERT's, is consistent with its rule-based nature and the
  challenges of noisy Reddit data. Its perfect precision for positive
  sentiment highlights its potential for identifying clear positive
  signals, though its overall accuracy suggests room for improvement.

### 2.3.5 Enhancing VADER's Performance

VADER's lower metrics (59.6% accuracy vs. FinBERT's 97.17%) stem from
its sensitivity to Reddit's informal language and lack of
domain-specific financial tuning. In order to enhance the performance of
VADER, a number of options can be considered:

- **Lexicon Expansion:** Extend the VADER dictionary with such financial
  terms as bullish and bearish as well as some popular Reddit slangs to
  better reflect the sentiment of the speech.

- **Preprocessing Improvements**: Enhance text cleaning by removing
  noise such as URLs and emojis and normalizing Reddit-specific
  abbreviations to reduce misclassifications.

<!-- -->

- **Hybrid Approach**: Combine VADER with a machine learning classifier
  for example with SVM trained on Reddit data to improve recall,
  particularly for positive and negative classes.

- **Threshold Tuning**: Adjust VADER's sentiment score thresholds to
  balance precision and recall, reducing overclassification of neutral
  sentiment. Despite its current metrics, VADER remains valuable for its
  computational efficiency and ability to process social media data,
  complementing FinBERT's focus on financial news. Future iterations of
  the project will implement these enhancements to improve VADER's
  performance while retaining its role in the pipeline.

### 2.3.6 Challenges and Considerations

Despite these advancements, several challenges persist:

- **Data Quality**: The accuracy of sentiment analysis is heavily
  dependent on the quality and relevance of the data sources.

- **Model Interpretability**: Complex models, particularly deep learning
  and LLMs, often operate as \"black boxes,\" making it difficult to
  interpret how decisions are made.

- **Dynamic Language**: The evolving nature of language, especially
  slang and colloquialisms in social media, poses challenges for
  maintaining up-to-date sentiment analysis models.

- **Temporal Relevance**: Ensuring that sentiment analysis captures the
  timely nature of market sentiment is crucial for its effectiveness in
  predictive modelling.

Addressing these challenges requires ongoing research and the
development of adaptive models that can evolve with the changing
landscape of financial communication.

## 2.4 Existing Sentiment Analysis Tools and Platforms

The financial market sentiment analysis tool market has changed a lot
with the development of NLP and the fact that the presence of
unstructured data has grown. They are designed to measure market
sentiment in order to use this to create trading strategies and look
after risks but could be generically divided into categories based upon
accessibility and target audience.

### 2.4.1 Commercial Platforms

Several sophisticated, proprietary platforms offer sentiment analysis as
a premium service, targeting institutional investors and large financial
firms:

- **Bloomberg Terminal:** Provides proprietary sentiment scores derived
  from a vast collection of news articles and social media, deeply
  integrated into its comprehensive financial analytics suite.

- **Thomson Reuters MarketPsych Indices:** Delivers real-time, tradable
  sentiment data indices extracted from news and social media, covering
  various asset classes and regions.

- **Sentifi:** Utilizes AI to analyse over 500 million tweets, news
  articles, and blogs to assess market sentiment, identify emerging
  risks, and track key opinion leaders.

While these platforms offer robust, high-quality features, their
significant subscription costs and often complex interfaces pose
substantial barriers to entry for retail investors, smaller
institutions, and academic researchers, creating a clear accessibility
gap.

### 2.4.2 Academic and Open-Source Tools

In contrast, the academic and open-source communities have developed
more accessible tools that form the bedrock of many sentiment analysis
applications:

- **FinBERT**: A pre-trained NLP model fine-tuned specifically for
  financial sentiment analysis, demonstrating high accuracy in
  classifying the unique lexicon of finance.

- **VADER (Valence Aware Dictionary and Sentiment Reasoner):** A lexicon
  and rule-based sentiment analysis tool highly effective for social
  media texts due to its tuning for slang and emoticons.

- **TextBlob**: Offers a simple API for common NLP tasks, including
  sentiment analysis, making it a popular choice for educational
  purposes and rapid prototyping.

These tools are transparent and cost-effective, but they often require
significant technical expertise to implement and may lack the real-time
processing capabilities, comprehensive data integration, and
user-friendly interfaces of their commercial counterparts. This project
aims to bridge that gap by building a sophisticated application on top
of these powerful open-source foundations.

### 2.4.3 Limitations and Challenges

Despite the advancements, several limitations persist:

- **Cost and Accessibility**: High subscription fees of commercial
  platforms limit access for individual investors and small firms.

- **Real-Time Processing**: Many tools struggle with real-time data
  processing, which is crucial for timely decision-making in volatile
  markets.

- **Data Quality and Noise**: Social media data, while rich in
  information, often contain noise and irrelevant content, posing
  challenges for accurate sentiment extraction.

- **Language and Context**: Understanding the nuances of financial
  language, including sarcasm, idioms, and domain-specific terminology,
  remains a complex task for NLP models.

### 2.4.4 Emerging Trends

Recent studies highlight the integration of advanced models and
techniques to address these challenges:

- The use of Large Language Models (LLMs), such as GPT-based
  architectures, has shown promise in capturing complex linguistic
  patterns and improving sentiment classification accuracy.

- Hybrid approaches combining rule-based methods with machine learning
  algorithms are being explored to enhance performance and
  interpretability.

- Efforts are underway to develop more transparent and explainable AI
  models to build trust and facilitate adoption among practitioners.

## 2.5 Role of APIs and Data Sources in Sentiment Analysis

With the overgrowth of digital media, the world is left with an overflow
of unstructured textual data that plays a crucial role in the financial
sentiment analysis. Access to this data is achieved through the
Application Programming Interfaces (APIs) which allow researchers and
practitioners to collect real-time data, that can capture the mood of
the people and the attitude of the market. These data sources are the
most critical criteria in determining the success of a particular
project in terms of it selection and handling.

### 2.5.1 Utilization of Free APIs

This project leverages a combination of free-tier APIs to construct a
diverse and robust dataset, ensuring the final product remains
accessible and reproducible. The chosen APIs provide complementary data
streams covering both professional financial reporting and organic
investor discussions for **a curated list of leading technology
stocks.**

- **Reddit (via PRAW):** The Python Reddit API Wrapper (PRAW) is used to
  extract posts and comments from financially relevant subreddits like
  r/wallstreetbets and r/stocks. Reddit provides an invaluable source of
  real-time, user-generated insights into retail investor sentiment and
  emotional responses to market events.

- **FinnHub:** Offers structured access to professional financial news
  articles and market data. FinnHub\'s focus on high-quality financial
  journalism makes it a reliable source for formal sentiment analysis.

- **Marketaux:** Aggregates financial news from a wide array of global
  sources, complementing FinnHub by broadening the scope of news
  coverage and introducing diverse perspectives.

- **NewsAPI:** Collects news articles from a vast range of mainstream
  publishers, enabling sentiment analysis on broader market events and
  news cycles that may indirectly impact technology stocks.

These APIs were strategically selected for their cost-free access, data
relevance, and their collective ability to provide a dual perspective on
market sentiment, contrasting the formal tone of financial news with the
informal, candid nature of social media.

### 2.5.2 Challenges in Using Free APIs

Free APIs are easy to access but they have a number of challenges as
well:

- **Limits on Rates and access to data**: Free tiers have restrictions
  on the number of requests; this may hold back the amount of data. The
  project overcomes this by batched processing at a set schedule time,
  so that better access to data can be achieved under the constraints of
  API.

- **Data Type**: Reddit is generally full of memes, slang, off-topic
  postings that the data needs to be cleaned well to make sure it is
  relevant. The APIs of the news might contain superfluous or irrelevant
  articles, and they should be deduplicated and scored.

- **Language and the Contextual Complexities**: How to be right about
  the sentiment requires being able to understand sarcasm ( prevalent on
  Reddit), financial jargon ( in news stories), that actual NLP models
  make hard. The project differentiates this through dedicated models
  such as FinBERT on news and VADER on Reddit, specific to their
  property.

- **Integration Complexity**: Multiple APIs need to be combined which
  implies a common data schema and proper synchronization, both of which
  are addressed by the project as a structured pipeline with timestamp
  normalization.

### 2.5.3 Ethical Considerations

The use of publicly available data through APIs raises important ethical
considerations:

- **Privacy and Consent**: Though the data used is publicly available,
  people may not anticipate that their Reddit posts or statements
  quoting news will be used to conduct financial analysis implying that
  such data must be handled properly not to reveal identities of people.

- **Transparency and Accountability**: The project is transparent, as
  uses of API and data processing stages are written in the open-source
  codebase, which promotes trust and adherence to ethical principles.

- **Bias and Fairness:** APIs can display bias in their sources of data,
  where Reddit user data is younger in age group and coverage on NewsAPI
  may be biased to publishing in the west and reduce the sentiment
  analysis potential. The project avoids this by cross-validating
  sentiments on numerous sources as well as using fairness-aware
  preprocessing.

## 2.6 Correlation Between Sentiment and Stock Prices

The correlation of the stock price movements with the moods of the
population has grown in observation over the last few years. The
developments in Natural Language Processing (NLP) and the spread of
digital platforms allowed scholars to conduct research on the way the
sentiment obtained based on a variety of sources impacts the financial
markets.

### 2.6.1 Empirical Evidence of Correlation

Several studies have investigated the correlation between sentiment and
stock prices:

- **Financial News Sentiment**: A study analysing financial news
  sentiments found a significant correlation between sentiment polarity
  and stock prices. For instance, the sentiment in news descriptions
  affected Microsoft\'s opening prices, while title sentiments
  influenced Tesla\'s opening prices. Similarly, Apple\'s closing prices
  were positively impacted by the sentiment in news titles.

- **Social Media Sentiment**: Research examining over three million
  stock-related tweets concluded that tweet-based sentiment strongly
  predicts market trends in both developed and emerging markets.

- **Combined Data Sources**: An ensemble deep learning model integrating
  stock prices and news sentiments demonstrated improved accuracy in
  predicting stock movements, highlighting the value of combining
  multiple data sources.

### 2.6.2 Statistical Methods Utilized

Researchers employ various statistical techniques to assess the
relationship between sentiment and stock prices:

- **Correlation Coefficients**: Pearson and Spearman correlation
  coefficients are commonly used to measure the strength and direction
  of the relationship between sentiment scores and stock price
  movements.

- **Regression Analysis**: Linear and logistic regression models help in
  understanding how sentiment variables predict stock returns.

- **Machine Learning Models**: Advanced models like Long Short-Term
  Memory (LSTM) networks and Random Forest classifiers have been
  utilized to capture complex patterns between sentiment and stock
  prices.

### 2.6.3 Conflicting Findings and Limitations

Despite promising results, some studies report inconsistent findings:

- **Lack of Significant Correlation**: A study analysing various
  industries and timeframes found a lack of significant correlation
  between sentiment and stock prices, with correlation coefficients
  ranging from -0.5 to 0.5 and averaging near zero.

- **Influence of External Factors**: Macroeconomic events, geopolitical
  issues, and company-specific news can overshadow sentiment effects,
  making it challenging to isolate sentiment's impact on stock prices.

- **Data Quality and Noise**: The unstructured nature of textual data
  from social media and news sources can introduce noise, affecting the
  accuracy of sentiment analysis.

While sentiment analysis offers valuable insights into market
psychology, its effectiveness in predicting stock prices varies across
studies. The integration of sentiment data with traditional financial
indicators and the use of advanced analytical models can enhance
predictive capabilities. However, researchers must account for external
factors and data quality issues to improve the reliability of
sentiment-based stock price predictions.

## 2.7 Gaps in Current Research

Although there have been prominent developments to sentiment analysis
(SA) in financial markets, there are a number of key gaps that remain a
detriment to its potential of predicting stock market dynamics
effectively.

1.  **Limited Predictive Power of Sentiment Analysis Alone**: Recent
    studies have highlighted that sentiment analysis, when used in
    isolation, lacks sufficient predictive power for stock price
    movements. For instance, a study analysing various industries and
    timeframes found a lack of significant correlation between sentiment
    and stock prices, with correlation coefficients ranging from -0.5 to
    0.5 and averaging near zero. This suggests that sentiment analysis
    should be integrated with other analytical methods to enhance
    prediction accuracy.

2.  **Challenges with Data Quality and Noise**: The Noise caused by the
    unstructured character of textual data derived from social media and
    news channels makes it difficult to implement sentiment analysis
    accurately. It has been observed that irrelevant or misinformed data
    can distort sentiment scores and hence show the need to use advanced
    preprocessing methods to eliminate noise, and bolster data quality.

3.  **Domain-Specific Language and Contextual Nuances**: Financial texts
    often contain domain-specific jargon and complex language
    structures, posing challenges for standard NLP models. The dynamic
    nature of language, including the use of sarcasm and
    context-dependent meanings, further complicates sentiment
    interpretation. This underscores the need for domain-adapted models
    that can accurately capture the nuances of financial language.

4.  **Lack of Standardized Methodologies**: There are no standardized
    methodologies to use in carrying out sentimental analysis within a
    financial context. Data source, preprocessing, and modeling
    differences cause inconsistency in results in different studies
    resulting in a lack of comparability in findings, and a lack of
    replicability in studies. Formalizing guidelines would help in
    making research findings reliable and comparable.

5.  **Ethical and Regulatory Considerations**: Sentiment analysis on
    publicly available data also entails ethical issues, the privacy
    issue being the key one and the factor of consent. Moreover,
    sentiment analysis as a part of trading systems can result in market
    manipulation and undesired results, so rules and regulations should
    be considered, and even ethical considerations should be considered.

6.  **Integration with Traditional Financial Indicators**: Although
    sentiment analysis can be helpful in showing the psychological state
    of markets, it has not been combined much with other financial
    measures. Integration of qualitative sentiment data with
    quantitative financial measures may be beneficial to predictive
    models, although problems of data alignment and model integration
    remain.

## 2.8 Summary

This chapter has reviewed the recent literature surrounding sentiment
analysis in financial markets, the psychological theories underpinning
investor behaviour, and the tools and technologies enabling
sentiment-driven insights. Beginning with the principles of behavioural
finance, we established that traditional financial models, such as the
Efficient Market Hypothesis (EMH), fall short of accounting for the
emotional and psychological dimensions of market dynamics. Seminal works
by Kahneman and Tversky, alongside real-world examples like the GameStop
surge, demonstrate how sentiment can drive irrational market behaviour.

Subsequent sections explored how natural language processing (NLP) has
empowered researchers to quantify these sentiments from sources like
social media, financial news, and online forums. Modern sentiment
analysis techniques ranging from lexicon-based models to deep learning
approaches like FinBERT and GPT-based systems have shown promising
results in identifying market sentiment trends. The evaluation of
FinBERT and VADER in this project confirms their suitability, with
FinBERT excelling in financial news analysis (97.17% accuracy) and VADER
providing a lightweight solution for Reddit data, despite lower metrics
(59.6% accuracy) that can be improved through lexicon expansion and
preprocessing. The project's use of free APIs (Reddit via PRAW, FinHub,
Marketaux, NewsAPI) ensures accessibility while addressing challenges
like rate limits through batch processing, aligning with the goal of
democratizing sentiment insights.

The review also assessed a range of existing sentiment platforms and
tools, highlighting their strengths but also emphasizing barriers such
as cost, limited accessibility, and weak real-time capabilities. The
role of APIs in democratizing access to sentiment data was examined,
alongside the technical and ethical challenges associated with their
use. Importantly, studies reviewed on the correlation between sentiment
and stock prices revealed mixed results, some indicating a strong link,
others showing minimal predictive power. These inconsistencies
underscore the need for more integrated, transparent, and adaptive
solutions that combine sentiment data with traditional financial
indicators.

In summary, the literature points to a growing consensus: sentiment is a
valuable but underutilized asset in financial analysis. There is a clear
gap in the availability of affordable, near real-time, open-source
dashboards that make sentiment insights accessible to non-institutional
investors. This gap directly supports the objectives of the proposed
project Stock Market Sentiment Dashboard: Analysis and Insights which
aims to address these limitations through a cost-effective, modular, and
scalable system. The next chapter will outline the functional and
Non-functional requirements for the proposed system.

# Chapter 3: Theoretical Framework

## 3.1 Overview

This chapter details the theoretical and technical framework designed to
power the Stock Market Sentiment Dashboard. It presents the
architectural blueprint for the project, outlining the sequence of
methods used for data collection, processing, analysis, and
visualization.

The framework is designed to be scalable. To clearly illustrate its core
components and logic, this chapter will demonstrate the process using a
focused and representative example: analyzing sentiment for the top 10
stocks in the Technology Select Sector Index (IXT) over a 7-day period.
The principles, libraries, and analytical steps detailed here are the
foundational methods that are applied to the project\'s full scope as
defined in Chapter 1. This approach allows for a coherent and practical
explanation of the framework\'s mechanics, supported by specific
examples and code implementations.

The framework employs a dual-model approach, using FinBERT for
structured financial news and VADER for informal Reddit posts. It then
aggregates these multi-source sentiment scores and correlates them with
stock price movements to explore market trends.

## 3.2 Justification of Tools and Libraries

This framework integrates a curated set of specialized Python libraries
and services to create a robust, end-to-end sentiment analysis pipeline.
Each component is selected for its specific strengths, ensuring a
comprehensive and reproducible workflow. The technologies are grouped by
their primary role in the framework.

- **Data Acquisition and Interfacing:**

<!-- -->

- **PRAW**: The Python Reddit API Wrapper is used to extract user-
  generated posts and comments from finance-related subreddits.

<!-- -->

- **API Client Libraries (finnhub-python, newsapi-python)**: These
  dedicated libraries provide a simplified, Pythonic interface to their
  respective news APIs, managing authentication and request formatting.

- **yfinance**: Leveraged to retrieve historical stock price data
  directly from Yahoo Finance, serving as the quantitative benchmark for
  correlation analysis.

- **Requests**: A fundamental library for making direct HTTP requests,
  used for interacting with APIs that may not have a dedicated Python
  client.

<!-- -->

- **Data Processing and Manipulation:**

<!-- -->

- **Pandas**: The core library for all data handling. It is used to
  structure data into DataFrames, and for cleaning, merging,
  aggregating, and time-series manipulation.

- **BeautifulSoup (bs4):** An essential tool for web scraping and data
  cleaning, used here to parse and extract clean text from the raw HTML
  content of news articles.

- **Regular Expressions (re):** Used for fine-grained text cleaning,
  such as removing URLs and other unwanted patterns from the raw text
  data.

<!-- -->

- **Sentiment Analysis and Machine Learning:**

<!-- -->

- **Transformers (Hugging Face):** Provides the architecture and tools
  to download and run state-of-the-art NLP models. This framework uses
  it to implement FinBERT.

- **PyTorch (torch):** The deep learning backend on which FinBERT
  operates. It handles complex tensor calculations and enables GPU
  acceleration for faster model inference.

- **NLTK (Natural Language Toolkit):** Used to implement the lexicon-
  and rule-based VADER sentiment analysis tool, which is highly
  effective for social media text.

- **Scikit-learn (sklearn):** A critical machine learning library used
  here for its robust evaluation metrics. Functions like accuracy_score,
  precision_score, recall_score, and classification_report are used to
  rigorously assess the performance of the sentiment analysis models.

<!-- -->

- **Data Visualization:**

<!-- -->

- **Matplotlib & Seaborn:** A powerful duo for generating static plots.
  They are used to create clear and insightful visualizations, such as
  dual-axis time-series charts, to compare sentiment trends against
  stock prices.

This comprehensive suite of tools ensures that every stage of the
analysis is handled by an industry-standard library, resulting in a
methodologically sound and technically robust framework.

## 3.3 Data Acquisition and API Configuration

The sentiment analysis pipeline will be based on building a strong and
effective data ingestion process that will access various external
sources. This entails granting access via API keys and carefully setting
up every service to access pertinent textual and monetary information.
The procedure guarantees a varied and modernizable dataset to analyze.

### 3.3.1 Principles of API Access

Access to external data services is enabled through API keys, which
serve as unique identifiers for the application. These keys are
fundamental for:

- **Authentication:** Verifying the application\'s identity to the API
  provider.

- **Authorization:** Granting access to specific data or
  functionalities.

- **Usage Tracking:** Monitoring request volumes to enforce rate limits
  and prevent abuse.

- **Security:** While API keys are essential for access, they are
  treated as sensitive credentials and **are not hard coded directly
  within the public codebase**. Instead, they are managed through secure
  environment variables or configuration files, the best practice for
  production deployments.

### 3.3.2 API Service Configuration

Each API used in this framework is configured to optimize data retrieval
for sentiment analysis, focusing on stock-specific content and temporal
relevance. Below are the key configurations and unique aspects for each
service:

1.  **Reddit API (PRAW) -- Community Sentiment**

- **Purpose:** To capture public sentiment from user-generated
  discussions on finance-related subreddits such as r/stocks,
  r/wallstreetbets, r/investing.

- **Configuration:** Requires a client_id, client_secret, and a
  user_agent. The user_agent string identifies the application to
  Reddit\'s servers. Authentication is managed via OAuth2, exchanging
  credentials for an access token.

- **Search Mechanism:** Queries posts using
  reddit.subreddit(subreddit).search(query, limit, time_filter). The
  time_filter is set to 'week' for recent posts, and a limit of 50 posts
  per subreddit is applied for the proof-of-concept.

- **Data Extraction:** Extracts post title and selftext (body),
  concatenating them into a single text field for sentiment analysis.
  Unix timestamps (created_utc) are converted to datetime objects for
  temporal filtering and alignment.

- **Rate Limiting:** PRAW automatically manages Reddit\'s rate limits by
  pausing execution, ensuring compliance.

2.  **NewsAPI -- Financial News Headlines**

- **Purpose:** To fetch recent financial news articles and headlines
  relevant to specific stock tickers or sectors from a broad range of
  publishers.

- **Configuration:** Access is granted via an API key, initialized
  through NewsApiClient(api_key).

- **API Endpoint:** Utilizes the get_everything endpoint with parameters
  for query (q), date range (from_param, to), and language (en). Dates
  are formatted as YYYY-MM-DD.

- **Data Extraction:** Retrieves article title, description (summary),
  and publishedAt (ISO 8601 timestamp). Title and description are
  concatenated for sentiment analysis.

- **Rate Limiting:** The free tier imposes a limit of 100 requests per
  day, necessitating efficient query management.

3.  **Finnhub API -- Real-Time Financial Data (News)**

- **Purpose:** To provide company-specific news articles, which are
  highly relevant for detailed sentiment analysis of individual stocks.

- **Configuration:** An API key is used to initialize the client
  (finnhub.Client(api_key)).

- **API Endpoint:** Queries news using company_news(stock, \_from, to)
  for a given ticker and date range.

- **Data Extraction:** Extracts headline, summary, and datetime (Unix
  timestamp) from each article. Headline and summary are combined into a
  single text field.

- **Rate Limiting:** The free tier allows 60 requests per minute,
  requiring careful pacing of queries, especially for multiple stocks.

4.  **Marketaux API -- Market News Aggregation**

- **Purpose:** To aggregate structured financial news, complementing
  other sources with broader coverage and sentiment tags.

- **Configuration:** An API token is initialized via Marketaux(api_key).

- **API Endpoint:** Retrieves news using get_news(symbol, from_date,
  to_date) for a ticker and date range. Dates are formatted YYYY-MM-DD.

- **Data Extraction:** Extracts title, description, and published_at
  (ISO 8601 timestamp). Title and description are concatenated.

- **Rate Limiting:** The free tier has a limit of 100 requests per day,
  like NewsAPI, requiring strategic data retrieval.

This multi-source data acquisition strategy, coupled with careful API
configuration and error handling, ensures a comprehensive and robust
foundation for the sentiment analysis pipeline.

## 3.4 Setup and Imports

The setup and imports phase establishes the foundation for the sentiment
analysis pipeline by configuring essential Python libraries and
environment settings. This phase ensures that tools for data collection,
preprocessing, sentiment analysis, evaluation, and visualization are
available, enabling a robust and reproducible workflow.

The pipeline integrates a curated set of Python libraries; each selected
for its specific role:

- **PRAW (Python Reddit API Wrapper)**: Facilitates interaction with
  Reddit's API, enabling retrieval of posts from finance-related
  subreddits while handling authentication and pagination.

- **finnhub-python**: Provides access to Finnhub's financial data API,
  simplifying queries for company-specific news.

- **newsapi-python**: Interfaces with NewsAPI to fetch general news
  articles, supporting keyword-based searches for stock tickers.

- **transformers**: Hugging Face's library for natural language
  processing, providing tokenization, model loading, and inference for
  FinBERT via a streamlined pipeline.

- **nltk (Natural Language Toolkit)**: Supports VADER sentiment analysis
  with a pre-trained lexicon tailored for social media text.

- **yfinance**: Retrieves historical stock price data from Yahoo Finance
  using a high-level API.

- **pandas**: Manages tabular data through DataFrames, enabling
  grouping, merging, and time-series operations.

- **matplotlib and seaborn**: Visualize sentiment and price trends, with
  Matplotlib offering low-level plotting control and Seaborn providing
  aesthetic, high-level visualizations.

- **sklearn.metrics**: Supplies evaluation metrics, including
  accuracy_score, precision_score, recall_score, f1_score, and
  classification_report, to assess model performance.

- **torch**: PyTorch library enabling GPU-accelerated tensor operations
  for FinBERT's inference.

- **datetime and timedelta**: Handle date and time intervals for the
  7-day data collection period.

- **re**: Supports text cleaning through regular expressions, such as
  removing URLs.

- **bs4 (BeautifulSoup)**: Extracts plain text from HTML news articles
  by removing markup.

Implementation involves installing external packages using !pip install
in Jupyter environments to download dependencies from PyPI. Libraries
are loaded with import statements, using aliases (e.g., pd for pandas)
for brevity and readability. The VADER lexicon is downloaded via
nltk.download(\'vader_lexicon\') to enable sentiment analysis for social
media text. Seaborn's style is configured with
sns.set(style=\'whitegrid\') to produce clear, consistent plots. This
setup ensures a modular, efficient, and compatible pipeline across
environments like JupyterLab and Colab.

Technical considerations ensure a reliable setup. Dependency management
is critical, as installing multiple packages, such as transformers and
sklearn, may introduce version conflicts, which are mitigated
automatically in environments like Colab but require thorough testing
for stability across other platforms. PyTorch enables GPU acceleration
for FinBERT's inference, necessitating compatible hardware and CUDA
setup to optimize performance. Evaluation metrics from sklearn.metrics
support macro-averaging, ensuring balanced assessment across sentiment
classes (positive, negative, neutral). This setup ensures a modular,
efficient, and compatible pipeline across environments like JupyterLab
and Colab.

+-----------------------------------------------------------------------+
| #pip install praw finnhub-python newsapi-python requests transformers |
| nltk scikit-learn pandas yfinance matplotlib seaborn torch            |
|                                                                       |
| import praw                                                           |
|                                                                       |
| import finnhub                                                        |
|                                                                       |
| from newsapi import NewsApiClient                                     |
|                                                                       |
| import requests                                                       |
|                                                                       |
| from transformers import AutoModelForSequenceClassification,          |
| AutoTokenizer, pipeline                                               |
|                                                                       |
| from nltk.sentiment.vader import SentimentIntensityAnalyzer           |
|                                                                       |
| from sklearn.metrics import accuracy_score, precision_score,          |
| recall_score, f1_score, classification_report                         |
|                                                                       |
| import nltk                                                           |
|                                                                       |
| import pandas as pd                                                   |
|                                                                       |
| import yfinance as yf                                                 |
|                                                                       |
| import matplotlib.pyplot as plt                                       |
|                                                                       |
| import seaborn as sns                                                 |
|                                                                       |
| from datetime import datetime, timedelta                              |
|                                                                       |
| import re                                                             |
|                                                                       |
| from bs4 import BeautifulSoup                                         |
|                                                                       |
| import torch                                                          |
|                                                                       |
| #nltk.download(\'vader_lexicon\')                                     |
|                                                                       |
| \# Set plotting style                                                 |
|                                                                       |
| sns.set(style=\'whitegrid\')                                          |
|                                                                       |
| print(\"✅ All imports successful!\")                                 |
+=======================================================================+

## 3.5 Define Stocks and Time Period

The definition of stocks and time period establishes the scope for the
sentiment analysis pipeline by selecting a focused set of stocks and a
time frame for data collection. The Technology Select Sector Index (IXT)
represents major technology companies, and its top 10 stocks, such as
AAPL and MSFT, provide a representative sample based on market
capitalization. A 7-day time period balances data volume with recency,
capturing short-term sentiment trends while ensuring sufficient data
within API rate limits, such as NewsAPI's 100 requests per day.

Implementation involves creating a Python list, stocks, containing
hard-coded tickers for the top 10 IXT stocks. The time period is defined
using the datetime library, setting the end date as the current date and
time with end_date = datetime.now() and calculating the start date as
start_date = end_date - timedelta(days=7). This creates a 7-day window
such as May 3--10, 2025, if run on May 10, 2025. The stocks list holds
string tickers, while start_date and end_date are datetime objects,
compatible with API queries and Pandas time-series operations. The
datetime library handles calendar rules, such as month boundaries and
leap years, ensuring accurate date computation.

Technical considerations include the use of a dynamic 7-day window,
achieved with datetime.now(), which ensures recency but requires careful
handling due to API restrictions, such as NewsAPI's limited historical
data access. Hard-coded tickers for the top 10 IXT stocks assume index
stability, but dynamic retrieval via APIs like yfinance could improve
accuracy in production. Time zone alignment is another consideration, as
datetime.now() uses local time, potentially misaligning with APIs using
UTC, such as NewsAPI, though daily granularity minimizes this issue.

This approach targets high-impact technology firms for relevance, uses a
fixed time period for feasibility, and simplifies the prototype with
hard-coded tickers, standardizing the scope across data sources like
Reddit, news APIs, and stock prices.

+-----------------------------------------------------------------------+
| \# Top 10 IXT stocks (approximate, based on market cap)               |
|                                                                       |
| stocks = \[\'AAPL\', \'MSFT\', \'NVDA\', \'GOOGL\', \'AMZN\',         |
| \'META\', \'TSLA\', \'INTC\', \'CSCO\', \'AMD\'\]                     |
|                                                                       |
| \# Time period: Last 7 days                                           |
|                                                                       |
| end_date = datetime.now()                                             |
|                                                                       |
| start_date = end_date - timedelta(days=7)                             |
+=======================================================================+

## 3.6 Data Collection

The data collection phase gathers raw text data from Reddit, Finnhub,
Marketaux, and NewsAPI to analyse sentiment for selected stocks over a
7-day period. These sources provide diverse perspectives: Reddit
captures informal public sentiment from social media, while Finnhub,
Marketaux, and NewsAPI offer professional and general news, enabling a
broad sentiment spectrum. The collected data is organized into Pandas
DataFrames with standardized columns (stock, date, text, source) for
efficient processing.

Data collection involves accessing APIs with authentication, such as API
keys, and query parameters like stock tickers and date ranges. JSON
responses are parsed into Python dictionaries, extracting relevant
fields like text and timestamps. Try-except blocks handle API errors,
such as rate limits and network issues, ensuring robustness. Lists of
dictionaries are converted to Pandas DataFrames, facilitating
streamlined manipulation and temporal alignment with the 7-day window.

### 3.6.1 Reddit Data Collection with PRAW

Reddit, a social media platform with finance-focused subreddits like
r/stocks, r/investing, and r/wallstreetbets, provides valuable public
sentiment on stocks. PRAW (Python Reddit API Wrapper) offers a Pythonic
interface to Reddit's API, enabling efficient retrieval of posts and
metadata. Its ease of use, extensive documentation, and support for
complex queries make it ideal for sentiment analysis.

The process begins with authentication, requiring a client_id,
client_secret, and user_agent (e.g., stock_sentiment_analysis) from
Reddit's developer portal. OAuth2 exchanges credentials for an access
token, enabling API calls. Posts are queried using
reddit.subreddit(subreddit).search(query, limit, time_filter) for each
stock ticker, with time_filter=\'week\' to limit results to the past 7
days and limit=50 to cap posts per subreddit. Reddit's Lucene-based
search ranks posts by relevance, based on term frequency and engagement,
such as upvotes.

For each post, the title, selftext (if available), and created_utc (Unix
timestamp) are extracted. The timestamp is converted to a datetime
object using datetime.fromtimestamp(t_utc) and filtered for the 7-day
window, with .date() extracting the date for aggregation. Title and
selftext are concatenated into a single text field, handling empty
selftext cases. Data is stored in a list of dictionaries with fields:
stock (ticker), date (timestamp's date), text (title + selftext), source
(Reddit), and converted to a Pandas DataFrame. Nested loops iterate over
stocks and subreddits (10 stocks × 3 subreddits = 30 queries), and
try-except blocks manage errors, logging issues for debugging. PRAW
pauses requests if Reddit's rate limit (60 requests/minute) is reached,
ensuring compliance.

+-----------------------------------------------------------------------+
| \# Initialize Reddit API                                              |
|                                                                       |
| reddit = praw.Reddit(                                                 |
|                                                                       |
|     client_id=\'YNKs2KS0EvyGflANCr7gDA\',                             |
|                                                                       |
|     client_secret=\'UCPPS8TiUr0U1lstXMElZ9utr2ad0g\',                 |
|                                                                       |
|     user_agent=\'StockSentimentDashboard:v1.0 (by                     |
| u/Able_Cobbler_5965)\'                                                |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# Fetch Reddit posts                                                 |
|                                                                       |
| reddit_data = \[\]                                                    |
|                                                                       |
| subreddits = \[\'stocks\', \'StockMarket\', \'investing\',            |
| \'wallstreetbets\'\]                                                  |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     for subreddit in subreddits:                                      |
|                                                                       |
|         try:                                                          |
|                                                                       |
|             for submission in                                         |
| reddit.subreddit(subreddit).search(f\'{stock}\', limit=50,            |
| time_filter=\'week\'):                                                |
|                                                                       |
|                 \# Start of submission processing                     |
|                                                                       |
|                 try:                                                  |
|                                                                       |
|                     timestamp =                                       |
| datetime.fromtimestamp(submission.created_utc)                        |
|                                                                       |
|                     if start_date \<= timestamp \<= end_date:         |
|                                                                       |
|                         reddit_data.append({                          |
|                                                                       |
|                             \'stock\': stock,                         |
|                                                                       |
|                             \'date\': timestamp.date(),               |
|                                                                       |
|                             \'text\': submission.title + \' \' +      |
| (submission.selftext or \'\'),                                        |
|                                                                       |
|                             \'source\': \'Reddit\'                    |
|                                                                       |
|                         })                                            |
|                                                                       |
|                 except Exception as e:                                |
|                                                                       |
|                     print(f\'Error processing submission for {stock}  |
| in {subreddit}: {e}\')                                                |
|                                                                       |
|         except Exception as e:                                        |
|                                                                       |
|             print(f\'Error fetching Reddit data for {stock} in        |
| {subreddit}: {e}\')                                                   |
|                                                                       |
| reddit_df = pd.DataFrame(reddit_data)                                 |
+:======================================================================+
| ![](media/image5.png){width="5.775751312335958in"                     |
| height="2.133643919510061in"}                                         |
+-----------------------------------------------------------------------+

### 3.6.2 Finnhub News Collection

Finnhub aggregates company-specific news articles from various sources,
offering a valuable resource for stock sentiment analysis due to its
financial relevance, structured JSON output, and reliable API. The
finnhub-python library provides a Python interface to query news data
linked to stock tickers.

The process involves initializing the client with an API key via
finnhub.Client(api_key), obtained from Finnhub's developer portal, to
authenticate HTTP requests. News is queried using company_news(stock,
\_from, to) for each ticker, with dates formatted as YYYY-MM-DD using
strftime(\'%Y-%m-%d\'). The API returns a JSON array of articles
containing fields like headline, summary, and datetime (Unix timestamp).
For each article, the headline and summary (if available) are
concatenated into a single text field, with article.get(\'summary\',
\'\') handling missing summaries. The Unix timestamp is converted to a
datetime object using datetime.fromtimestamp(t_unix) and its date
extracted for daily aggregation. Data is stored in a list of
dictionaries with fields: stock, date, text, source (Finnhub), and
converted to a Pandas DataFrame. Try-except blocks catch errors, such as
invalid tickers or rate limits, logging issues for debugging. The
process iterates over stocks, querying news sequentially for each
ticker.

+-----------------------------------------------------------------------+
| \# Initialize FinHub API                                              |
|                                                                       |
| finnhub_client =                                                      |
| finnhub.Client(api_key=\'d0cgff9r01ql2j3d1bj0d0cgff9r01ql2j3d1bjg\')  |
|                                                                       |
| \# Fetch FinHub news                                                  |
|                                                                       |
| finhub_data = \[\]                                                    |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     try:                                                              |
|                                                                       |
|         news = finnhub_client.company_news(stock,                     |
| \_from=start_date.strftime(\'%Y-%m-%d\'),                             |
| to=end_date.strftime(\'%Y-%m-%d\'))                                   |
|                                                                       |
|         for article in news:                                          |
|                                                                       |
|             timestamp =                                               |
| datetime.fromtimestamp(article\[\'datetime\'\])                       |
|                                                                       |
|             finhub_data.append({                                      |
|                                                                       |
|                 \'stock\': stock,                                     |
|                                                                       |
|                 \'date\': timestamp.date(),                           |
|                                                                       |
|                 \'text\': article\[\'headline\'\] + \' \' +           |
| (article.get(\'summary\', \'\') or \'\'),                             |
|                                                                       |
|                 \'source\': \'FinHub\'                                |
|                                                                       |
|             })                                                        |
|                                                                       |
|     except Exception as e:                                            |
|                                                                       |
|         print(f\'Error fetching FinHub data for {stock}: {e}\')       |
|                                                                       |
| finhub_df = pd.DataFrame(finhub_data)                                 |
+:======================================================================+
| ![](media/image6.png){width="5.9006944444444445in"                    |
| height="3.0854166666666667in"}                                        |
+-----------------------------------------------------------------------+

### 3.6.3 Marketaux News Collection

Marketaux, a financial news API, aggregates ticker-specific articles,
providing a curated dataset for sentiment analysis due to its
ticker-specific focus and structured output. The Marketaux library
offers a Python client to query news by ticker and date range.

The process initializes the client with an API token via
Marketaux(api_key), obtained from Marketaux's dashboard, to authenticate
requests. Articles are queried using get_news(symbol, from_date,
to_date), with dates formatted as YYYY-MM-DD using
strftime(\'%Y-%m-%d\'). The API returns a JSON object with a data field
containing an array of articles. For each article, the title,
description (if available), and published_at (ISO 8601 timestamp) are
extracted. The title and description are concatenated into a single text
field, with article.get(\'description\', \'\') handling missing
descriptions. The timestamp is parsed using datetime.strptime(t_iso,
\'%Y-%m-%dT%H:%M:%S.%fZ\') and its date extracted for aggregation. Data
is stored in a list of dictionaries with fields: stock, date, text,
source (Marketaux), and converted to a Pandas DataFrame. Try-except
blocks catch errors, such as invalid parameters or rate limits, using
news.get(\'data\', \[\]) to safely access the data field. The process
iterates over stocks, querying news sequentially.

+-----------------------------------------------------------------------+
| \# Marketaux API configuration                                        |
|                                                                       |
| MARKETAUX_API_KEY = \'aqvsldqCVLcD5AzQ4CJLprX32Jdq1Sgq6H6FnwNM\'      |
|                                                                       |
| MARKETAUX_BASE_URL = \'https://api.marketaux.com/v1/news/all\'        |
|                                                                       |
| \# Fetch Marketaux news (minimal data for prototype)                  |
|                                                                       |
| marketaux_data = \[\]                                                 |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     try:                                                              |
|                                                                       |
|         print(f\'Fetching Marketaux news for {stock}\...\')           |
|                                                                       |
|         \# Prepare API request parameters                             |
|                                                                       |
|         params = {                                                    |
|                                                                       |
|             \'Api_token\': MARKETAUX_API_KEY,                         |
|                                                                       |
|             \'symbols\': stock,                                       |
|                                                                       |
|             \'published_after\': start_date.strftime(\'%Y-%m-%d\'),   |
|                                                                       |
|             \'published_before\': end_date.strftime(\'%Y-%m-%d\'),    |
|                                                                       |
|             \'limit\': 3  # Fetch up to 3 articles per stock          |
|                                                                       |
|         }                                                             |
|                                                                       |
|         \# Make API request with timeout                              |
|                                                                       |
|         response = requests.get(MARKETAUX_BASE_URL, params=params,    |
| timeout=10)                                                           |
|                                                                       |
|         response.raise_for_status()                                   |
|                                                                       |
|         news = response.json().get(\'data\', \[\])                    |
|                                                                       |
|         for article in news\[:3\]:  # Ensure max 3 articles           |
|                                                                       |
|             timestamp =                                               |
| datetime.strptime(article\[\'published_at\'\],                        |
| \'%Y-%m-%dT%H:%M:%S.%fZ\')                                            |
|                                                                       |
|             marketaux_data.append({                                   |
|                                                                       |
|                 \'stock\': stock,                                     |
|                                                                       |
|                 \'date\': timestamp.date(),                           |
|                                                                       |
|                 \'text\': article\[\'title\'\] + \' \' +              |
| (article.get(\'description\', \'\') or \'\'),                         |
|                                                                       |
|                 \'source\': \'Marketaux\'                             |
|                                                                       |
|             })                                                        |
|                                                                       |
|         print(f\'Fetched {len(news\[:3\])} articles for {stock}\')    |
|                                                                       |
|     except Exception as e:                                            |
|                                                                       |
|         print(f\'Error fetching Marketaux data for {stock}: {e}\')    |
|                                                                       |
| \# Convert to DataFrame                                               |
|                                                                       |
| marketaux_df = pd.DataFrame(marketaux_data)                           |
|                                                                       |
| print(f\'Total Marketaux articles collected: {len(marketaux_df)}\')   |
+:======================================================================+
| ![](media/image7.png){width="5.691554024496938in"                     |
| height="3.984785651793526in"}                                         |
+-----------------------------------------------------------------------+

### 3.6.4 NewsAPI Data Collection

NewsAPI aggregates articles from thousands of sources, including major
publishers and blogs, supporting keyword-based searches for stock ticker
mentions. The newsapi-python library provides a Python client to query
news, offering broad coverage, ease of use, and clear JSON responses,
making it suitable for capturing general news sentiment.

The process initializes the client with an API key via
NewsApiClient(api_key), obtained from NewsAPI's dashboard, to
authenticate requests. Articles are queried using get_everything(q,
from_param, to, language) for each ticker, with parameters including the
query (ticker), start and end dates (formatted as YYYY-MM-DD), and
language (en for English). The API returns a JSON object with an
articles field containing an array of articles. For each article, the
title, description (if available), and publishedAt (ISO 8601 timestamp)
are extracted. The title and description are concatenated into a single
text field, with article.get(\'description\',\'\') handling missing
descriptions. The timestamp is parsed using datetime.strptime(t_iso,
\'%Y-%m-%dT%H:%M:%SZ\') and its date extracted for aggregation. Data is
stored in a list of dictionaries with fields: stock, date, text, source
(NewsAPI), and converted to a Pandas DataFrame. Try-except blocks catch
errors, such as query failures or rate limits, logging issues for
debugging. The process iterates over stocks, querying articles
sequentially for each ticker.

+-----------------------------------------------------------------------+
| \# Initialize NewsAPI                                                 |
|                                                                       |
| newsapi = NewsApiClient(api_key=\'7334eef3efc34ebaa1b65970e6909a00\') |
|                                                                       |
| \# Fetch NewsAPI articles                                             |
|                                                                       |
| newsapi_data = \[\]                                                   |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     try:                                                              |
|                                                                       |
|         articles = newsapi.get_everything(q=stock,                    |
| from_param=start_date.strftime(\'%Y-%m-%d\'),                         |
| to=end_date.strftime(\'%Y-%m-%d\'), language=\'en\')                  |
|                                                                       |
|         for article in articles\[\'articles\'\]:                      |
|                                                                       |
|             timestamp = datetime.strptime(article\[\'publishedAt\'\], |
| \'%Y-%m-%dT%H:%M:%SZ\')                                               |
|                                                                       |
|             newsapi_data.append({                                     |
|                                                                       |
|                 \'stock\': stock,                                     |
|                                                                       |
|                 \'date\': timestamp.date(),                           |
|                                                                       |
|                 \'text\': article\[\'title\'\] + \' \' +              |
| (article.get(\'description\', \'\') or \'\'),                         |
|                                                                       |
|                 \'source\': \'NewsAPI\'                               |
|                                                                       |
|             })                                                        |
|                                                                       |
|     except Exception as e:                                            |
|                                                                       |
|         print(f\'Error fetching NewsAPI data for {stock}: {e}\')      |
|                                                                       |
| newsapi_df = pd.DataFrame(newsapi_data)                               |
+:======================================================================+
| ![](media/image8.png){width="5.7854593175853015in"                    |
| height="2.3530172790901136in"}                                        |
+-----------------------------------------------------------------------+

## 3.7 Text Preprocessing

The text preprocessing phase refines raw text data from Reddit, Finnhub,
Marketaux, and NewsAPI to prepare it for sentiment analysis using
FinBERT for news data and VADER for Reddit posts. By removing noise and
standardizing formats, preprocessing ensures text is clean, relevant,
and compatible with each model's input requirements, enhancing sentiment
classification accuracy.

Preprocessing employs regular expressions to remove URLs and special
characters, BeautifulSoup to extract plain text from HTML content, and
whitespace normalization to collapse multiple spaces and newlines into
single spaces. These steps are applied to the text column of Pandas
DataFrames using the apply method, storing results in a new cleaned_text
column. Technical considerations include the robustness of the regular
expression pattern http\\S+\|www\\S+, which matches URLs but may miss
edge cases like malformed URLs, and the performance of BeautifulSoup,
which handles malformed HTML but may be slower than regex for simple
cases.

### 3.7.1 Preprocessing for FinBERT (Finnhub, Marketaux, NewsAPI)

FinBERT, a BERT-based model fine-tuned for financial texts, classifies
sentiment as positive, negative, or neutral, leveraging contextual
embeddings to capture word relationships (Araci, 2019). Its
preprocessing requires minimal intervention to preserve financial
context while removing noise, ensuring accurate sentiment analysis of
news data from Finnhub, Marketaux, and NewsAPI.

The process removes URLs using re.sub(r\'http\\S+\|www\\S+\', \'\',
text) to eliminate irrelevant links, strips HTML tags with
BeautifulSoup(text, \'html.parser\').get_text() to extract plain text,
and normalizes whitespace using \' \'.join(text.split()) to collapse
multiple spaces, tabs, or newlines. Financial entities like tickers,
monetary values, and percentages are preserved to maintain semantic
meaning for FinBERT's contextual understanding. Tokenization is deferred
to FinBERT's tokenizer, loaded via
AutoTokenizer.from_pretrained(\'ProsusAI/finbert\'), which handles
subword tokenization and special tokens during sentiment analysis.
Stemming and lemmatization are avoided to align with FinBERT's training
on raw financial text. Technical considerations include the risk of
truncating articles exceeding FinBERT's 512-token limit, which may lose
context, requiring careful handling during tokenization.

The preprocess_finbert function sequentially applies URL removal, HTML
stripping, and whitespace normalization, returning cleaned text. This
function is applied to the text column of DataFrames (finhub_df,
marketaux_df, newsapi_df) using
df\[\'text\'\].apply(preprocess_finbert), storing results in
cleaned_text. This approach ensures context preservation by retaining
financial terms, focuses on noise removal to leverage FinBERT's
tokenizer, and addresses common noise like URLs and HTML in news data
for robust sentiment analysis.

+-----------------------------------------------------------------------+
| \# Load FinBERT tokenizer                                             |
|                                                                       |
| tokenizer = AutoTokenizer.from_pretrained(\'ProsusAI/finbert\')       |
|                                                                       |
| def preprocess_finbert(text):                                         |
|                                                                       |
|     \# Remove URLs                                                    |
|                                                                       |
|     text = re.sub(r\'http\\S+\|www\\S+\', \'\', text)                 |
|                                                                       |
|     \# Remove HTML tags                                               |
|                                                                       |
|     text = BeautifulSoup(text, \'html.parser\').get_text()            |
|                                                                       |
|     \# Remove extra whitespace                                        |
|                                                                       |
|     text = \' \'.join(text.split())                                   |
|                                                                       |
|     return text                                                       |
|                                                                       |
| \# Apply preprocessing                                                |
|                                                                       |
| for df in \[finhub_df, marketaux_df, newsapi_df\]:                    |
|                                                                       |
|     df\[\'cleaned_text\'\] = df\[\'text\'\].apply(preprocess_finbert) |
+=======================================================================+

### 3.7.2 Preprocessing for VADER (Reddit)

VADER (Valence Aware Dictionary and Sentiment Reasoner), a lexicon-based
tool designed for social media texts, uses a dictionary of
valence-scored words and rules to handle negation, punctuation, and
emoticons (Hutto & Gilbert, 2014). Its preprocessing simplifies Reddit
text to align with VADER's case-insensitive lexicon while preserving
sentiment cues like informal language and punctuation, ensuring accurate
sentiment scoring.

The process converts text to lowercase using text.lower() for consistent
lexicon matching, removes URLs with re.sub(r\'http\\S+\|www\\S+\', \'\',
text), and filters out emojis, hashtags, and symbols using
re.sub(r\'\[\^a-z0-9\\s.,!?\]\', \'\', text), retaining alphanumeric
characters and punctuation like commas, periods, exclamation points, and
question marks for VADER's intensity scoring. Whitespace is normalized
using \' \'.join(text.split()) to collapse multiple spaces and newlines.
Informal language and punctuation such as (awesome!!!) are preserved,
avoiding stemming or lemmatization to leverage VADER's rule-based
design. Technical considerations include the regular expression pattern
\[\^a-z0-9\\s.,!?\], which removes non-essential characters while
preserving sentiment-relevant punctuation, and the need to handle
Reddit's diverse language, such as slang and memes, which demands robust
cleaning for edge cases. VADER's reliance on punctuation for intensity
requires selective retention of specific characters.

The preprocess_vader function applies lowercasing, URL removal,
character filtering, and whitespace normalization, returning cleaned
text. This function is applied to the text column of reddit_df using
reddit_df\[\'text\'\].apply(preprocess_vader), storing results in
cleaned_text. This approach ensures lexicon compatibility, preserves
social media-specific features, and minimizes preprocessing to leverage
VADER's design.

+-----------------------------------------------------------------------+
| def preprocess_vader(text):                                           |
|                                                                       |
|     \# Lowercase                                                      |
|                                                                       |
|     text = text.lower()                                               |
|                                                                       |
|     \# Remove URLs                                                    |
|                                                                       |
|     text = re.sub(r\'http\\S+\|www\\S+\', \'\', text)                 |
|                                                                       |
|     \# Remove special characters, keep alphanumeric and basic         |
| punctuation                                                           |
|                                                                       |
|     text = re.sub(r\'\[\^a-z0-9\\s.,!?\]\', \'\', text)               |
|                                                                       |
|     \# Remove extra whitespace                                        |
|                                                                       |
|     text = \' \'.join(text.split())                                   |
|                                                                       |
|     return text                                                       |
|                                                                       |
| \# Apply preprocessing                                                |
|                                                                       |
| reddit_df\[\'cleaned_text\'\] =                                       |
| reddit_df\[\'text\'\].apply(preprocess_vader)                         |
+=======================================================================+

## 3.8 Sentiment Analysis

The sentiment analysis phase classifies text from Reddit, Finnhub,
Marketaux, and NewsAPI as positive, negative, or neutral to gauge public
perception of stocks. FinBERT, a BERT-based model fine-tuned for
financial contexts, processes news data from Finnhub, Marketaux, and
NewsAPI, while VADER, optimized for social media, analyses Reddit posts.
This step assigns sentiment labels and probability scores to each text,
enriching datasets for aggregation and correlation with stock prices.

The process loads pre-trained models, with FinBERT accessed via the
*transformers* library and VADER via *nltk*. Cleaned text from the
cleaned_text column of DataFrames is processed to compute sentiment
scores, which are stored in new columns such as sentiment_label and
sentiment_score. FinBERT generates contextual embeddings for news text,
producing probabilities for each sentiment class, while VADER applies
its lexicon-based rules to score Reddit posts, accounting for informal
language and punctuation. Try-except blocks handle processing failures,
such as empty text or memory issues, logging errors for debugging.
Technical considerations include managing FinBERT's computational
requirements, as its transformer architecture demands significant memory
and GPU resources, and ensuring VADER's lexicon aligns with Reddit's
informal language for accurate scoring. This approach leverages
FinBERT's financial specificity and VADER's social media suitability,
integrating sentiment data into DataFrames for further analysis.

### 3.8.1 FinBERT Sentiment Analysis

FinBERT, a BERT-based model fine-tuned for financial sentiment analysis,
classifies news text from Finnhub, Marketaux, and NewsAPI as positive,
negative, or neutral, leveraging contextual embeddings to capture
nuanced financial language (Araci, 2019). Its architecture features a
BERT backbone with 12 transformer layers, including multi-head
self-attention and feed-forward networks, processing text
bidirectionally to produce 768-dimensional token representations. The
model is pre-trained on general corpora and fine-tuned on financial
datasets like Financial PhraseBank to optimize for financial terms.
Input text is tokenized into subword units using WordPiece, adding
\[CLS\] and \[SEP\] tokens, with truncation to 512 tokens, and the
output passes the \[CLS\] token's embedding through a linear layer and
softmax to produce class probabilities.

### 3.8.1.1 FinBERT Mathematical Foundations

- **Token Embeddings**:\
  $$\left\lbrack E = E_{token} + E_{segment} + E_{position} \right\rbrack$$
  where $E_{\text{token}}$ is the word embedding,
  $E_{\text{segment }}$distinguishes sentences, and
  $E_{\text{position}}\ $encodes position.

- **Self-Attention**:\
  $$\left\lbrack \text{Attention}(Q,K,V) = \text{softmax}\left( \frac{QK^{T}}{\sqrt{d_{k}}} \right)V \right\rbrack$$
  where (Q), (K), (V) are query, key, and value matrices, and (d_k = 64)
  is the attention head dimension.

- **Transformer Layers**:\
  $${\left\lbrack h' = \text{LayerNorm}\left( h + \text{Attention}(h) \right) \right\rbrack
  }{\left\lbrack h^{''} = \text{LayerNorm}\left( h' + \text{FFN}\left( h' \right) \right) \right\rbrack
  }$$where (h) is the input embedding, and$\ \left( \text{FFN} \right)$
  is a two-layer neural network.

- **Classification**:\
  $$\left\lbrack z = W \cdot h_{\text{[CLS]}} + b \right\rbrack$$
  where (W) is a (3 \\times 768) weight matrix, and (b) is a bias
  vector.

- **Softmax**:\
  $$\left\lbrack P_{i} = \frac{e^{z_{i}}}{\sum_{j}^{}e^{z_{j}}} \right\rbrack$$
  where (z_i) is the logit for class (i).

The implementation loads FinBERT via
AutoModelForSequenceClassification.from_pretrained(\'ProsusAI/finbert\')
with 3 output classes, tokenizing text with tokenizer (text,
return_tensors=\'pt\', truncation=True, max_length=512, padding=True) to
generate input_ids, attention_mask, and token_type_ids. Inference
retrieves logits (1 × 3) using model(\*\*inputs), applying softmax
conversion with
$\left\lbrack P_{i} = \frac{e^{z_{i}}}{\sum_{j}^{}e^{z_{j}}} \right\rbrack$
via outputs.logits.softmax(dim=1) and converting to NumPy. For numerical
stability, the softmax is adjusted with
$\left\lbrack P_{i} = \frac{e^{z_{i} - \max(z)}}{\sum_{j}^{}e^{z_{j} - \max(z)}} \right\rbrack$
to prevent overflow. The highest-probability class is assigned using
labels\[scores.argmax()\] with labels = \[\'positive\', \'negative\',
\'neutral\'\]. Try-except blocks return \'neutral\' and zero scores for
failures, and the finbert_sentiment function applies tokenization,
inference, and post-processing, integrating results into DataFrame
columns sentiment and scores. Technical considerations include WordPiece
tokenization, where subwords are split and attention_mask ignores
padding tokens, softmax stability requiring maximum logit subtraction,
and inference overhead due to FinBERT's 110M parameters, which demand
significant computation.

The finbert_sentiment function manages memory with .detach() during
tensor conversion and supports batching for efficiency. This approach
ensures financial context accuracy, captures complex relationships in
news text, and adapts to varied texts due to extensive pre-training.

+--------------------------------------------------------------------------+
| \# Check for GPU and set device                                          |
|                                                                          |
| device = torch.device(\"cuda\" if torch.cuda.is_available() else         |
| \"cpu\")                                                                 |
|                                                                          |
| \# Load tokenizer and model, then move model to GPU                      |
|                                                                          |
| tokenizer = AutoTokenizer.from_pretrained(\'ProsusAI/finbert\')          |
|                                                                          |
| model =                                                                  |
| AutoModelForSequenceClassification.from_pretrained(\'ProsusAI/finbert\') |
|                                                                          |
| model.to(device)                                                         |
|                                                                          |
| model.eval()  # Optional but helps with speed and memory usage           |
|                                                                          |
| def finbert_sentiment(text):                                             |
|                                                                          |
|     try:                                                                 |
|                                                                          |
|         \# Tokenize and move inputs to the same device as the model      |
|                                                                          |
|         inputs = tokenizer(text, return_tensors=\'pt\', truncation=True, |
| max_length=512, padding=True).to(device)                                 |
|                                                                          |
|         with torch.no_grad():  # Disable gradient computation for        |
| inference                                                                |
|                                                                          |
|             outputs = model(\*\*inputs)                                  |
|                                                                          |
|             scores =                                                     |
| outputs.logits.softmax(dim=1).detach().cpu().numpy()\[0\]  # Move back   |
| to CPU for numpy                                                         |
|                                                                          |
|         labels = \[\'positive\', \'negative\', \'neutral\'\]             |
|                                                                          |
|         sentiment = labels\[scores.argmax()\]                            |
|                                                                          |
|         return sentiment, scores                                         |
|                                                                          |
|     except Exception as e:                                               |
|                                                                          |
|         print(f\'Error in FinBERT sentiment analysis: {e}\')             |
|                                                                          |
|         return \'neutral\', \[0, 0, 0\]                                  |
|                                                                          |
| \# Apply FinBERT to your DataFrames                                      |
|                                                                          |
| for df in \[finhub_df, marketaux_df, newsapi_df\]:                       |
|                                                                          |
|     df\[\[\'sentiment\', \'scores\'\]\] =                                |
| df\[\'cleaned_text\'\].apply(lambda x: pd.Series(finbert_sentiment(x)))  |
+:=========================================================================+
| \# Display sample results for each DataFrame                             |
|                                                                          |
| print(\"FinHub DataFrame Sample (Sentiment Results):\")                  |
|                                                                          |
| print(finhub_df\[\[\'stock\', \'date\', \'text\', \'sentiment\',         |
| \'scores\'\]\].head(5))                                                  |
|                                                                          |
| print(\"\\nMarketaux DataFrame Sample (Sentiment Results):\")            |
|                                                                          |
| print(marketaux_df\[\[\'stock\', \'date\', \'text\', \'sentiment\',      |
| \'scores\'\]\].head(5))                                                  |
|                                                                          |
| print(\"\\nNewsAPI DataFrame Sample (Sentiment Results):\")              |
|                                                                          |
| print(newsapi_df\[\[\'stock\', \'date\', \'text\', \'sentiment\',        |
| \'scores\'\]\].head(5))                                                  |
+--------------------------------------------------------------------------+
| ![](media/image9.png){width="5.776865704286964in"                        |
| height="5.2096095800524935in"}                                           |
+--------------------------------------------------------------------------+

The provided output shows the results of a sentiment analysis conducted
using the FinBERT model on financial news data from three different
sources: finhub_df, marketaux_df, and newsapi_df. Each entry includes
the stock ticker, publication date, news text, predicted sentiment label
(positive, negative, or neutral), and corresponding sentiment scores.
The sentiment scores represent the model's confidence in each category,
allowing for a nuanced understanding of market-related news. The results
reveal varying sentiments across datasets, with some headlines showing
strong positive tones, while others are more neutral or mixed. This
analysis can help gauge market sentiment around specific stocks and
inform investment decisions based on public perception and news trends.

### 3.8.2 VADER Sentiment Analysis

VADER (Valence Aware Dictionary and Sentiment Reasoner), a rule-based
sentiment analysis tool optimized for social media, computes sentiment
scores using a lexicon and heuristic rules, making it ideal for
analysing Reddit posts due to its lightweight and interpretable design
(Hutto & Gilbert, 2014). Its architecture includes a lexicon of
approximately 7,500 words, emoticons, and slang with valence scores on a
\[-4, 4\] scale (e.g., great = 1.9, terrible = -2.0), supplemented by
rules for punctuation, negation, capitalization, booster words, and
conjunctions. Punctuation amplifies intensity such as +0.292 per
exclamation point, negation inverts sentiment, uppercase words increase
intensity (+0.733), booster words like very scale valence (+0.5), and
conjunctions like but emphasize latter clauses. The output generates
positive, negative, neutral (0 to 1), and compound (-1 to 1) scores.

The mathematical foundation normalizes the sum of valence scores to
compute the compound score with
$\left\lbrack \text{compound} = \text{normalize}\left( \sum\text{valence\_scores} \right) \right\rbrack$,
where
$\left\lbrack \text{normalize}(x) = \frac{x}{\sqrt{x^{2} + \alpha}},\quad\alpha = 15 \right\rbrack$.
The implementation initializes VADER via SentimentIntensityAnalyzer()
with its lexicon and rules, processing text with
sia.polarity_scores(text) to tokenize, match lexicon entries, apply
rules, and compute scores. Sentiment is assigned based on the compound
score: positive if \> 0.05, negative if \< -0.05, otherwise neutral. The
vader_sentiment function returns the sentiment label and scores (\[pos,
neg, neu\]), with try-except blocks returning neutral and zero scores
for errors. Results are integrated into reddit_df\[\'cleaned_text\'\],
stored in sentiment and scores columns. Technical considerations include
lexicon matching, where simple word splitting may miss complex phrases
or new slang, rule application with empirically tuned weights affecting
accuracy, and normalization sensitivity due to the heuristic (\\alpha =
15).

The vader_sentiment function structures scoring, classification, and
output formatting, extracting scores via dictionary keys (e.g.,
scores\[\'compound\'\]) and using if-elif-else for thresholding. This
approach ensures social media fit, provides computational efficiency,
and offers transparent, interpretable scores.

+-----------------------------------------------------------------------+
| \# Initialize VADER                                                   |
|                                                                       |
| sia = SentimentIntensityAnalyzer()                                    |
|                                                                       |
| def vader_sentiment(text):                                            |
|                                                                       |
|     try:                                                              |
|                                                                       |
|         scores = sia.polarity_scores(text)                            |
|                                                                       |
|         compound = scores\[\'compound\'\]                             |
|                                                                       |
|         if compound \> 0.05:                                          |
|                                                                       |
|             sentiment = \'positive\'                                  |
|                                                                       |
|         elif compound \< -0.05:                                       |
|                                                                       |
|             sentiment = \'negative\'                                  |
|                                                                       |
|         else:                                                         |
|                                                                       |
|             sentiment = \'neutral\'                                   |
|                                                                       |
|         return sentiment, \[scores\[\'pos\'\], scores\[\'neg\'\],     |
| scores\[\'neu\'\]\]                                                   |
|                                                                       |
|     except Exception as e:                                            |
|                                                                       |
|         print(f\'Error in VADER sentiment analysis: {e}\')            |
|                                                                       |
|         return \'neutral\', \[0, 0, 0\]                               |
|                                                                       |
| \# Apply VADER                                                        |
|                                                                       |
| reddit_df\[\[\'sentiment\', \'scores\'\]\] =                          |
| reddit_df\[\'cleaned_text\'\].apply(lambda x:                         |
| pd.Series(vader_sentiment(x)))                                        |
+:======================================================================+
| \# Display sample results for Reddit DataFrame (VADER Sentiment)      |
|                                                                       |
| print(\"Reddit DataFrame Sample (VADER Sentiment Results):\")         |
|                                                                       |
| print(reddit_df\[\[\'stock\', \'date\', \'text\', \'sentiment\',      |
| \'scores\'\]\].head(5))                                               |
+-----------------------------------------------------------------------+
| ![](media/image10.png){width="5.707096456692914in"                    |
| height="1.6047725284339458in"}                                        |
+-----------------------------------------------------------------------+

The output shows the results of applying the VADER sentiment analysis
tool to Reddit posts. Each row represents a post, with columns
indicating the sentiment label (\"positive\", \"negative\", or
\"neutral\") and the corresponding sentiment scores (pos, neg, neu).
These scores reflect the proportion of positive, negative, and neutral
language in each post. The analysis helps gauge the overall tone and
investor sentiment expressed in financial discussions on Reddit.

### 3.8.3 FinBERT Sentiment Analysis Evaluation

The evaluation of FinBERT's sentiment analysis performance compares its
predictions to a labelled ground truth dataset of 2,264 financial
sentences (1,391 neutral, 570 positives, 303 negative) to quantify
accuracy and robustness. Metrics such as accuracy, precision, recall,
and F1-score assess classification performance across these classes,
while a confusion matrix visualizes prediction errors, providing
insights into model strengths and weaknesses.

The process loads the labelled data by reading sentences and labels from
a ground truth file using a function like load_labeled_sentences,
mapping sentiments (positive, neutral, negative) to numerical values (2,
1, 0). Predictions are run on the test set in batches of 16 using
FinBERT, loaded via AutoModelForSequenceClassification and AutoTokenizer
from ProsusAI/finbert with GPU support, converting predicted labels to
numerical values. Metrics are computed using *sklearn.metrics* functions
with macro-averaging for balanced multi-class evaluation, and a
confusion matrix is visualized as a heatmap with *seaborn* and
*matplotlib*. Technical considerations include efficient batch
processing, which enhances speed and memory usage with precise indexing
to align predictions, and macro-averaging, which ensures fair evaluation
despite the neutral-heavy distribution (61.4% neutral, 25.2% positive,
13.4% negative), with the confusion matrix highlighting classification
patterns for targeted improvements.

Calculations include accuracy with
$\left\lbrack \text{Accuracy} = \frac{\text{Number of correct predictions}}{\text{Total number of predictions}} \right\rbrack$,
precision with
$\left\lbrack \text{Precision} = \frac{1}{C}\sum_{c = 1}^{C}\frac{\text{True }\text{Positives}_{c}}{\text{True }\text{Positives}_{c} + \text{False }\text{Positives}_{c}} \right\rbrack$
where (C = 3) is the number of classes*, recall with*
$\left\lbrack \text{Recall} = \frac{1}{C}\sum_{c = 1}^{C}\frac{\text{True }\text{Positives}_{c}}{\text{True }\text{Positives}_{c} + \text{False }\text{Negatives}_{c}} \right\rbrack$*,
and F1-score with*
$\left\lbrack \text{F1} = \frac{1}{C}\sum_{c = 1}^{C}\frac{2 \cdot \text{Precision}_{c} \cdot \text{Recall}_{c}}{\text{Precision}_{c} + \text{Recall}_{c}} \right\rbrack$.
This approach provides a comprehensive evaluation, visual insight into
error patterns, and scalability for large datasets.

+--------------------------------------------------------------------------+
| \# Load labeled data                                                     |
|                                                                          |
| def load_labeled_sentences(file_path):                                   |
|                                                                          |
|     sentences = \[\]                                                     |
|                                                                          |
|     labels = \[\]                                                        |
|                                                                          |
|     label_map = {\'positive\': 2, \'neutral\': 1, \'negative\': 0}       |
|                                                                          |
|     with open(file_path, \'r\', encoding=\'latin-1\') as f:              |
|                                                                          |
|         for line in f:                                                   |
|                                                                          |
|             if \'@\' in line:                                            |
|                                                                          |
|                 sentence, tag = line.strip().rsplit(\'@\', 1)            |
|                                                                          |
|                 if tag in label_map:                                     |
|                                                                          |
|                     sentences.append(sentence)                           |
|                                                                          |
|                     labels.append(label_map\[tag\])                      |
|                                                                          |
|     return sentences, labels                                             |
|                                                                          |
| \# Load FinBERT (ProsusAI) and force GPU                                 |
|                                                                          |
| device = 0 if torch.cuda.is_available() else -1                          |
|                                                                          |
| print(\"Using device:\", \"GPU\" if device == 0 else \"CPU\")            |
|                                                                          |
| model =                                                                  |
| AutoModelForSequenceClassification.from_pretrained(\'ProsusAI/finbert\') |
|                                                                          |
| tokenizer = AutoTokenizer.from_pretrained(\'ProsusAI/finbert\')          |
|                                                                          |
| finbert_pipeline = pipeline(\"sentiment-analysis\", model=model,         |
| tokenizer=tokenizer, device=device)                                      |
|                                                                          |
| label_map = {\"positive\": 2, \"neutral\": 1, \"negative\": 0}           |
|                                                                          |
| \# Run predictions                                                       |
|                                                                          |
| file_path = \"Sentences_AllAgree.txt\"  # Ground truth file              |
|                                                                          |
| sentences, true_labels = load_labeled_sentences(file_path)               |
|                                                                          |
| print(\"Running FinBERT (ProsusAI) on test set\... (this may take a few  |
| minutes)\")                                                              |
|                                                                          |
| predicted_labels = \[\]                                                  |
|                                                                          |
| batch_size = 16                                                          |
|                                                                          |
| for i in range(0, len(sentences), batch_size):                           |
|                                                                          |
|     batch = sentences\[i:i+batch_size\]                                  |
|                                                                          |
|     results = finbert_pipeline(batch)                                    |
|                                                                          |
|     batch_preds = \[label_map\[r\[\'label\'\].lower()\] for r in         |
| results\]                                                                |
|                                                                          |
|     predicted_labels.extend(batch_preds)                                 |
|                                                                          |
| \# Evaluation Metrics                                                    |
|                                                                          |
| accuracy = accuracy_score(true_labels, predicted_labels)                 |
|                                                                          |
| precision = precision_score(true_labels, predicted_labels,               |
| average=\'macro\')                                                       |
|                                                                          |
| recall = recall_score(true_labels, predicted_labels, average=\'macro\')  |
|                                                                          |
| f1 = f1_score(true_labels, predicted_labels, average=\'macro\')          |
|                                                                          |
| print(f\"Accuracy:  {accuracy:.4f}\")                                    |
|                                                                          |
| print(f\"Precision: {precision:.4f}\")                                   |
|                                                                          |
| print(f\"Recall:    {recall:.4f}\")                                      |
|                                                                          |
| print(f\"F1 Score:  {f1:.4f}\")                                          |
|                                                                          |
| print(\"\\nClassification Report:\")                                     |
|                                                                          |
| print(classification_report(true_labels, predicted_labels,               |
| target_names=\[\"negative\", \"neutral\", \"positive\"\]))               |
|                                                                          |
| \# Confusion Matrix                                                      |
|                                                                          |
| from sklearn.metrics import confusion_matrix                             |
|                                                                          |
| cm = confusion_matrix(true_labels, predicted_labels)                     |
|                                                                          |
| sns.heatmap(cm, annot=True, fmt=\'d\', cmap=\'Blues\',                   |
|                                                                          |
|             xticklabels=\[\"negative\", \"neutral\", \"positive\"\],     |
|                                                                          |
|             yticklabels=\[\"negative\", \"neutral\", \"positive\"\])     |
|                                                                          |
| plt.title(\"Confusion Matrix\")                                          |
|                                                                          |
| plt.xlabel(\"Predicted\")                                                |
|                                                                          |
| plt.ylabel(\"True\")                                                     |
|                                                                          |
| plt.show()                                                               |
+:=========================================================================+
| ![](media/image11.png){width="5.716751968503937in"                       |
| height="3.37795384951881in"}                                             |
+--------------------------------------------------------------------------+

**FinBERT Evaluation**: FinBERT was evaluated on a dataset of 2,264
financial sentences (1,391 neutral, 570 positives, 303 negative). The
model achieved:

- **Accuracy**: 97.17%

- **Precision**: 95.85%

- **Recall**: 97.59%

- **F1-Score**: 96.25%

**Class Insights:**

- **Negative**: Precision 0.91, Recall 0.98, F1 0.94 excellent recall
  ensures most negatives are identified.

- **Neutral**: Precision 1.00, Recall 0.97, F1 0.98 perfect precision,
  no misclassifications as neutral.

- **Positive**: Precision 0.95, Recall 0.98, F1 0.96 strong performance
  across metrics. FinBERT's high accuracy and balanced performance
  across classes confirm its reliability for financial news sentiment
  analysis, supporting its role in generating precise inputs for stock
  sentiment trends.

### 3.8.4 VADER Sentiment Analysis Evaluation

The evaluation of VADER's sentiment analysis performance compares its
predictions to a synthetic ground truth dataset of 1,000 Reddit
comments, manually labelled as positive, neutral, or negative, to
confirm its effectiveness for social media sentiment analysis. Metrics
such as accuracy, precision, recall, and F1-score assess performance,
while a confusion matrix visualizes true versus predicted labels,
ensuring reliable inputs for stock sentiment trends.

The process loads the dataset from Reddit_SyntheticGroundTruth.csv using
*pandas*, mapping labels (positive, neutral, negative) to numerical
values (2, 1, 0) with label_map = {\'negative\': 0, \'neutral\': 1,
\'positive\': 2}. VADER applies polarity_scores to compute compound
scores, assigning labels with a threshold of ±0.05 via vader_predict.
Metrics are calculated using *sklearn.metrics* with macro-averaging for
balanced evaluation, and a confusion matrix heatmap is generated with
*seaborn* and *matplotlib*. Technical considerations include
thresholding at ±0.05 to balance sensitivity and specificity for social
media texts, macro-averaging to accommodate potential imbalances in the
synthetic dataset, and the confusion matrix providing clear insights
into classification accuracy and errors.

Calculations include accuracy with
$\left\lbrack \text{Accuracy} = \frac{\text{Number of correct predictions}}{\text{Total number of predictions}} \right\rbrack$,
precision with
$\left\lbrack \text{Precision} = \frac{1}{C}\sum_{c = 1}^{C}\frac{\text{True }\text{Positives}_{c}}{\text{True }\text{Positives}_{c} + \text{False }\text{Positives}_{c}} \right\rbrack\ $where
( C = 3 ), recall with\
$\left\lbrack \text{Recall} = \frac{1}{C}\sum_{c = 1}^{C}\frac{\text{True }\text{Positives}_{c}}{\text{True }\text{Positives}_{c} + \text{False }\text{Negatives}_{c}} \right\rbrack$,and
F1-score with\
$\left\lbrack \text{F1} = \frac{1}{C}\sum_{c = 1}^{C}\frac{2 \cdot \text{Precision}_{c} \cdot \text{Recall}_{c}}{\text{Precision}_{c} + \text{Recall}_{c}} \right\rbrack$.
This approach ensures efficient evaluation, actionable insights from the
confusion matrix, and lightweight processing suitable for the
1,000-comment dataset.

+-----------------------------------------------------------------------+
| \# Initialize VADER                                                   |
|                                                                       |
| vader = SentimentIntensityAnalyzer()                                  |
|                                                                       |
| \# Load your manually labeled CSV                                     |
|                                                                       |
| \# Expect columns: comment_id, text, true_label  (where true_label ∈  |
| {\'positive\',\'neutral\',\'negative\'})                              |
|                                                                       |
| df = pd.read_csv(\"Reddit_SyntheticGroundTruth.csv\")                 |
|                                                                       |
| \#  Map to numeric                                                    |
|                                                                       |
| label_map = {\'negative\': 0, \'neutral\': 1, \'positive\': 2}        |
|                                                                       |
| df\[\'y_true\'\] = df\[\'true_label\'\].map(label_map)                |
|                                                                       |
| \#  Get VADER predictions                                             |
|                                                                       |
| def vader_predict(txt):                                               |
|                                                                       |
|     c = vader.polarity_scores(txt)\[\'compound\'\]                    |
|                                                                       |
|     if c \>=  0.05: return 2                                          |
|                                                                       |
|     if c \<= -0.05: return 0                                          |
|                                                                       |
|     return 1                                                          |
|                                                                       |
| df\[\'y_pred\'\] = df\[\'text\'\].apply(vader_predict)                |
|                                                                       |
| \#  Evaluate                                                          |
|                                                                       |
| print(\"Accuracy: \", accuracy_score(df.y_true, df.y_pred))           |
|                                                                       |
| print(\"Precision:\", precision_score(df.y_true, df.y_pred,           |
| average=\'macro\'))                                                   |
|                                                                       |
| print(\"Recall:   \", recall_score(df.y_true, df.y_pred,              |
| average=\'macro\'))                                                   |
|                                                                       |
| print(\"F1 Score: \", f1_score(df.y_true, df.y_pred,                  |
| average=\'macro\'))                                                   |
|                                                                       |
| print(\"\\n\", classification_report(df.y_true, df.y_pred,            |
| target_names=\[\'neg\',\'neu\',\'pos\'\]))                            |
|                                                                       |
| \#  Confusion matrix                                                  |
|                                                                       |
| cm = confusion_matrix(df.y_true, df.y_pred)                           |
|                                                                       |
| sns.heatmap(cm, annot=True, fmt=\'d\', cmap=\'Blues\',                |
|                                                                       |
|             xticklabels=\[\'neg\',\'neu\',\'pos\'\],                  |
|                                                                       |
|             yticklabels=\[\'neg\',\'neu\',\'pos\'\])                  |
|                                                                       |
| plt.xlabel(\"Predicted\"); plt.ylabel(\"True\"); plt.show()           |
+:======================================================================+
| ![](media/image12.png){width="5.778536745406824in"                    |
| height="3.504613954505687in"}                                         |
+-----------------------------------------------------------------------+

VADER Evaluation: VADER was assessed on a synthetic dataset of 1,000
Reddit comments, manually labeled as positive, neutral, or negative. The
model achieved:

- **Accuracy**: 59.6%

- **Precision**: 67.57%

- **Recall**: 60.19%

- **F1-Score**: 59.39%

**Class Insights:**

- **Negative**: Precision 0.56, Recall 0.49, F1 0.52, balanced
  misclassifications between negative and neutral.

- **Neutral**: Precision 0.47, Recall 0.82, F1 0.60, high recall but low
  precision, indicating overclassification as neutral.

- **Positive**: Precision 1.00, Recall 0.49, F1 0.66, perfect precision
  but low recall, missing many positives. VADER's performance, while
  lower than FinBERT's, is consistent with its rule-based nature and the
  challenges of noisy Reddit data. Its perfect precision for positive
  sentiment highlights its potential for identifying clear positive
  signals, though its overall accuracy suggests room for improvement.

## 3.9 Aggregation

Aggregation consolidates sentiment scores from Reddit, FinHub,
Marketaux, and NewsAPI into a unified dataset, computing daily averages
for each stock to summarize public sentiment trends. A 3-day moving
average smooths short-term fluctuations, creating a time-series dataset
for correlation with stock prices and enabling trend analysis and
financial comparison.

The process begins with concatenating DataFrames (reddit_df, finhub_df,
marketaux_df, newsapi_df) into a single DataFrame using consistent
columns (stock, date, text, source, sentiment, scores), followed by
mapping sentiment labels (positive, neutral, negative) to numerical
scores (+1, 0, -1). Data is then grouped by stock and date to compute
mean sentiment scores, and a 3-day moving average is applied to smooth
the data, handling partial windows at the start with a minimum period
of 1. The aggregated and smoothed data is stored in a new DataFrame for
further analysis. Technical considerations include ensuring data
alignment for successful concatenation, optimizing the groupby operation
for large datasets using Pandas' internals, and managing moving average
edge cases where partial windows are present.

- Calculations involve the mean sentiment score with
  $\left\lbrack \text{sentiment\_score}s,d = \frac{1}{Ns,d}\sum_{i = 1}^{N_{s,d}}{\text{sentiment\_score}i} \right\rbrack\ $*where
  ( N*{s,d} ) is the number of texts for stock ( s ) on date ( d ),
  and$\ \left( \text{sentiment\_score}_{i} \in - 1,0,1 \right)$*, and
  the moving average with*

> $$\left\lbrack \text{sentiment\_ma}s,d = \frac{1}{\min(3,k)}\sum_{}^{}{j = d - k + 1^{d}S_{s,j}} \right\rbrack$$
> where
> $\left( k = \min\left( 3,\text{number of available days} \right) \right)$,
> and (S\_{s,j}) is the sentiment score for stock (s) on day (j).
>
> This approach offers simplicity with interpretable mean scores, noise
> reduction through the 3-day moving average, and flexibility for
> alternative aggregation methods.

+-----------------------------------------------------------------------+
| \# Combine all data                                                   |
|                                                                       |
| all_data = pd.concat(\[reddit_df, finhub_df, marketaux_df,            |
| newsapi_df\], ignore_index=True)                                      |
|                                                                       |
| \# Convert sentiment to numerical scores                              |
|                                                                       |
| sentiment_map = {\'positive\': 1, \'neutral\': 0, \'negative\': -1}   |
|                                                                       |
| all_data\[\'sentiment_score\'\] =                                     |
| all_data\[\'sentiment\'\].map(sentiment_map)                          |
|                                                                       |
| \# Aggregate by stock and date                                        |
|                                                                       |
| agg_data = all_data.groupby(\[\'stock\',                              |
| \'date\'\])\[\'sentiment_score\'\].mean().reset_index()               |
|                                                                       |
| \# Apply 3-day moving average for smoothing                           |
|                                                                       |
| agg_data\[\'sentiment_ma\'\] =                                        |
| agg_data.groupby(\'stock\')\[\'sentiment_score\'\].transform(lambda   |
| x: x.rolling(window=3, min_periods=1).mean())                         |
+=======================================================================+

## 3.10 Fetch Stock Prices

This step retrieves historical stock price data for selected stocks over
a 7-day period, aligning with sentiment data, using the yfinance library
to access Yahoo Finance's API. Daily closing prices serve as the
financial benchmark for correlating sentiment trends, enabling analysis
of public sentiment's alignment with market performance.

The process involves querying Yahoo Finance via yfinance for historical
prices by iterating over stock tickers, specifying a start and end date
range, and extracting the Close price and Date. Dates are converted to a
date-only format, and the resulting data is combined into a single
DataFrame. Error handling manages issues like invalid tickers or network
problems with logging to ensure continuity. Technical considerations
include the reliability of Yahoo Finance's unofficial API, which may
face rate limits or downtime mitigated by yfinance's retries, handling
approximately 5 trading days within the 7-day period due to weekend
closures, and ensuring date formatting compatibility with datetime
inputs for the API.

Calculations include the closing price defined as *\*
$\left\lbrack \text{Close}_{s,d} = \text{Stock price for stock }s\text{ at market close on date }d \right\rbrack$,and
date conversion with
$\left\lbrack \text{date} = \left\lfloor \text{Date} \right\rfloor \right\rbrack\ $where
(\\lfloor \\cdot \\rfloor) extracts the date portion of a datetime. This
approach offers simplicity through yfinance's abstraction, focuses on
the standard closing price metric, and ensures robustness with error
handling for pipeline continuity.

+-----------------------------------------------------------------------+
| \# Fetch stock prices                                                 |
|                                                                       |
| price_data = \[\]                                                     |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     try:                                                              |
|                                                                       |
|         ticker = yf.Ticker(stock)                                     |
|                                                                       |
|         hist = ticker.history(start=start_date, end=end_date)         |
|                                                                       |
|         hist = hist.reset_index()                                     |
|                                                                       |
|         hist\[\'stock\'\] = stock                                     |
|                                                                       |
|         hist\[\'date\'\] = hist\[\'Date\'\].dt.date                   |
|                                                                       |
|         price_data.append(hist\[\[\'stock\', \'date\', \'Close\'\]\]) |
|                                                                       |
|     except Exception as e:                                            |
|                                                                       |
|         print(f\'Error fetching price data for {stock}: {e}\')        |
|                                                                       |
| price_df = pd.concat(price_data, ignore_index=True)                   |
+=======================================================================+

## 3.11 Visualization

Visualization plots smoothed sentiment scores and stock prices over a
7-day period using dual-axis plots to compare trends, facilitating
qualitative analysis of sentiment-price relationships. This step employs
Matplotlib and Seaborn to generate plots for each stock, saving them as
image files to support documentation and interpretation.

The process merges agg_data and price_df via an inner join on stock and
date to align trading days, creating dual-axis plots for each stock with
sentiment_ma on the left y-axis (blue) and Close on the right y-axis
(red). Customization includes labels, titles, legends, and layout
adjustments, with plots saved as PNG files named by stock ticker. Error
handling skips empty datasets, logging issues for debugging. Technical
considerations include managing different scales (sentiment: \[-1, 1\],
price: dollars) with twinx(), handling data gaps from the inner join
that reduce data to approximately 5 trading days per stock, and freeing
memory by closing figures with plt.close().

Calculations define merged data as

$\lbrack"\{ merged\_ data\}\  = \ \{(s,\ d)\  \mid s\  \in "\{ stocks\},\ d\  \in "\{ trading\ days\},\ "\{ sentiment\_ ma\}\{ s,d\}\ "\{\ exists\},\ "\{ Close\}\{ s,d\}\ "\{\ exists\}\}\rbrack$,
ensuring temporal alignment via inner join. This approach provides
clarity through dual axis plots, automates plot generation for all
stocks, and ensures persistence by saving images for external review.

+-----------------------------------------------------------------------+
| \# Merge sentiment and price data                                     |
|                                                                       |
| merged_data = pd.merge(agg_data, price_df, on=\[\'stock\',            |
| \'date\'\], how=\'inner\')                                            |
|                                                                       |
| \# Plot for each stock                                                |
|                                                                       |
| for stock in stocks:                                                  |
|                                                                       |
|     stock_data = merged_data\[merged_data\[\'stock\'\] == stock\]     |
|                                                                       |
|     if stock_data.empty:                                              |
|                                                                       |
|         print(f\'No data for {stock}\')                               |
|                                                                       |
|         continue                                                      |
|                                                                       |
|     fig, ax1 = plt.subplots(figsize=(10, 6))                          |
|                                                                       |
|     \# Plot sentiment                                                 |
|                                                                       |
|     ax1.plot(stock_data\[\'date\'\], stock_data\[\'sentiment_ma\'\],  |
| \'b-\', label=\'Sentiment (MA)\')                                     |
|                                                                       |
|     ax1.set_xlabel(\'Date\')                                          |
|                                                                       |
|     ax1.set_ylabel(\'Sentiment Score\', color=\'b\')                  |
|                                                                       |
|     ax1.tick_params(axis=\'y\', labelcolor=\'b\')                     |
|                                                                       |
|     \# Plot stock price                                               |
|                                                                       |
|     ax2 = ax1.twinx()                                                 |
|                                                                       |
|     ax2.plot(stock_data\[\'date\'\], stock_data\[\'Close\'\], \'r-\', |
| label=\'Stock Price\')                                                |
|                                                                       |
|     ax2.set_ylabel(\'Stock Price (\$)\', color=\'r\')                 |
|                                                                       |
|     ax2.tick_params(axis=\'y\', labelcolor=\'r\')                     |
|                                                                       |
|     \# Title and legend                                               |
|                                                                       |
|     plt.title(f\'Sentiment vs. Stock Price for {stock}\')             |
|                                                                       |
|     fig.legend(loc=\'upper center\', bbox_to_anchor=(0.5, -0.05),     |
| ncol=2)                                                               |
|                                                                       |
|     plt.tight_layout()                                                |
|                                                                       |
|     \# Save plot                                                      |
|                                                                       |
|     plt.savefig(f\'{stock}\_sentiment_price.png\')                    |
|                                                                       |
|     plt.close()                                                       |
+=======================================================================+

## 3.12 Pipeline Challenges and Mitigation Strategies

Throughout the development of the sentiment analysis pipeline, various
challenges arise across data setup, collection, preprocessing, sentiment
analysis, aggregation, stock price retrieval, and visualization phases.
Initial setup and imports face delays from installing large libraries
like transformers and torch in cloud environments, version mismatches
causing runtime errors, and high memory demands requiring hardware
optimization, addressed through rigorous testing and resource
management. Defining stocks and time periods encounters selection bias
from static tickers, the 7-day window missing long-term trends, and API
date formatting issues, mitigated by dynamic ticker updates and
standardized formats. Data collection struggles with irrelevant results
from keyword searches, sparse data for lesser-known stocks, speculative
bias from Reddit, missing summaries, and rate limit constraints, tackled
with preprocessing, optimized queries, and error logging.

Text preprocessing deals with ticker overlap in non-financial contexts,
complex HTML parsing, performance bottlenecks, sarcasm and slang
misinterpretation by VADER, and over-cleaning risks, addressed by
refined regex, efficient parsing, and cautious preprocessing
adjustments. Sentiment analysis faces FinBERT's computational intensity,
VADER's nuanced sentiment gaps, unreliable scores from short texts,
FinBERT's truncation and misclassification issues, VADER's sarcasm
blindness, and evaluation dataset imbalances, managed with batch
optimization, context-aware preprocessing, error checks, and data
augmentation. Aggregation contends with data imbalances skewing
averages, the 3-day moving average obscuring rapid shifts, and equal
source weighting, resolved through normalization, adjustable windows,
and weighted strategies. Fetching stock prices grapples with weekend
data gaps, reliance on Yahoo Finance's unstable API, and data loss from
errors, addressed with interpolation, API monitoring, and robust error
handling. Finally, visualization handles scale disparities between
sentiment and price, missing data skipping plots, and interpretability
risks, mitigated by normalized scales, data validation, and statistical
support.

These challenges are systematically addressed to enhance pipeline
reliability, ensuring accurate sentiment-price analysis through adaptive
techniques, error management, and validation strategies tailored to each
phase.

# Chapter 4: Requirements 

## 4.1 Overview 

Functional Requirements define specific behaviours or functions a
system, application, or product must perform. They describe what the
system should do, focusing on user interactions, processes, data
manipulation, and outputs. These requirements are typically written in
clear, unambiguous language to guide developers, testers, and
stakeholders.

### 4.1.1 Why We Need Functional Requirements 

1.  **Establish Clear Expectations**: They provide a detailed blueprint
    of the system\'s intended functions, ensuring that all stakeholders
    have a shared understanding of the system\'s capabilities.

2.  **Guide Development and Testing**: Functional requirements serve as
    a foundation for system design, development, and testing, enabling
    developers to build the system correctly and testers to verify its
    functionality.

3.  **Facilitate Communication**: By clearly documenting what the system
    should do, functional requirements enhance communication among
    project team members, stakeholders, and users, reducing
    misunderstandings and misinterpretations.

4.  **Support Project Management**: They help in defining the project
    scope, estimating costs and timelines, and managing changes, thereby
    contributing to effective project planning and control.

The quality attributes of the system are stated as **Non-Functional
Requirements (NFRs)**. They specify the way the system is expected to
execute its tasks with the emphasis made on such criteria as
performance, usability, reliability and security of the system. NFRs
make a system effective, robust, and functional.

Projects running without functional and Non-Functional requirements are
likely to face ineffective communication, design gaps, or products that
do not pass user expectations.

## 4.2 Functional Requirements

### 4.2.1 User Functional Requirements

[]{#_z4fgvob2eotf .anchor}Table 4.1: User Functional Requirements

  --------------- ----------------------- --------------------------------
   **Requirement       **Functional               **Description**
       ID**            Requirement**      

       U-FR1      Users shall be able to   Users can view an interactive
                    view the sentiment     dashboard displaying sentiment
                        dashboard.         scores and stock prices for a
                                              curated list of leading
                                                 technology stocks.

       U-FR2      Users should be able to    Users can select different
                   select a time range.          analysis windows,
                                            including 1-day, 7-day, and
                                              14-day views, to explore
                                           sentiment-price correlations.

       U-FR3      Users should be able to  Users can filter all data and
                     filter by stock.       visualizations by selecting
                                          specific stock symbols from the
                                                     watchlist.

       U-FR4      Users should be able to  Users can view dual-axis plots
                   compare sentiment vs.  that overlay sentiment trends on
                       stock price.        top of stock price movements.

       U-FR5      Users should be able to    Users can access a dynamic
                     view the dynamic        module that calculates and
                   correlation analysis.    displays Pearson correlation
                                            values between sentiment and
                                           stock prices for the selected
                                                stock and timeframe.

       U-FR6      Users should be able to    Users (Administrators) can
                      evaluate model      review performance metrics like
                         accuracy.          accuracy, F1-score, etc. for
                                             sentiment analysis models.

       U-FR7      Users should be able to Users (Administrators) can input
                    configure API keys.     or update API keys for data
                                          sources like Reddit, FinHub, and
                                          NewsAPI through a configuration
                                                     interface.

       U-FR8      Users should be able to    Users (Administrators) can
                     update the stock       modify the stock list being
                        watchlist.                   analyzed.

       U-FR9      Users should be able to    Users (Administrators) can
                    manage data storage    specify where data is stored,
                         settings.         such as in local file systems,
                                             SQLite, or cloud storage.

      U-FR10      Users should be able to    Users (Administrators) can
                     view system logs.      access logs detailing system
                                          activity, data pipeline errors,
                                                  or API warnings.
  --------------- ----------------------- --------------------------------

### 4.2.2 System Functional Requirements

[]{#_Toc199184011 .anchor}Table 4.2: System Functional Requirements

  --------------- ----------------------- --------------------------------
   **Requirement       **Functional               **Description**
       ID**            Requirement**      

      SY-FR1       System should be able    The system fetches data from
                      to run the data       sources like Reddit, FinHub,
                   collection pipeline.       Marketaux, and NewsAPI,
                                           supporting manual triggers or
                                                  scheduled runs.

      SY-FR2       System should be able   The system processes noisy or
                  to preprocess raw data.   unstructured textual data by
                                             cleaning, normalizing, and
                                             filtering it for analysis.

      SY-FR3       System should be able    The system applies VADER to
                   to perform sentiment   Reddit data and FinBERT to news
                         analysis.        articles to classify sentiment.

      SY-FR4       System should be able     The system saves processed
                    to store sentiment         sentiment results in a
                         results.           structured format, such as a
                                              database or file system.

      SY-FR5       System should be able      The system automatically
                  to schedule batch data   retrieves data from configured
                         fetching.         sources at regular intervals.

      SY-FR6       System should be able  The system manages and throttles
                    to handle API rate         API requests to ensure
                          limits.           compliance with rate limits.

      SY-FR7       System should be able  The system aligns sentiment data
                       to normalize       timestamps with stock price data
                        timestamps.        to enable accurate correlation
                                                     analysis.

      SY-FR8       System should be able      The system automatically
                        to trigger         refreshes visualizations when
                  visualization updates.    new data becomes available.

      SY-FR9       System should be able       The system records all
                      to log pipeline        activities related to data
                        operations.          collection, analysis, and
                                                    processing.
  --------------- ----------------------- --------------------------------

**4.3 Non-Functional Requirements (NFRs)**

NFRs define the quality attributes and operational constraints of the
system, ensuring it is efficient, usable, and reliable.

[]{#_Toc201534930 .anchor}Table 4.3: Non-Functional Requirements

  --------------------------------------------------------------------------
  **NFR ID**       **Category**      **Requirement**
  ---------------- ----------------- ---------------------------------------
  NFR-1            Performance       The interactive dashboard
                                     visualizations and correlation results
                                     shall load in under 10 seconds for a
                                     standard user query.

  NFR-2            Usability         The user interface shall be designed
                                     for clarity and ease of use, aiming to
                                     minimize the number of steps required
                                     for a user to access key analytical
                                     insights.

  NFR-3            Reliability       The data collection pipeline shall be
                                     designed for robustness, incorporating
                                     error handling and logging to manage
                                     potential API failures or transient
                                     network issues gracefully.

  NFR-4            Scalability       The system architecture should support
                                     the addition of new stocks to the
                                     watchlist without requiring significant
                                     changes to the codebase.

  NFR-5            Maintainability   The codebase must be well-documented
                                     with comments and a clear structure to
                                     facilitate future updates and bug
                                     fixes.

  NFR-6            Security          API keys and any other sensitive
                                     credentials must be stored securely and
                                     not hard coded in the source files.
  --------------------------------------------------------------------------

# 

# Chapter 5: Analysis

## 5.1 Overview

System analysis is the process of studying a system or its parts to
identify its objectives, and it is a problem-solving technique that
improves the system and ensures that all the components of the system
work efficiently to accomplish their purpose (Pfleeger & Atlee, 2009).
This chapter provides a detailed examination of the requirements
outlined in Chapter 4, translating them into analytical models that
guide system design and implementation. By decomposing each requirement
into its core components, we can ensure a thorough understanding of the
system\'s intended behaviour.

This analysis is presented through two key software engineering
artifacts: Use-Case Models and detailed Use-Case Descriptions. Use-case
models provide a high-level visual summary of user-system interactions,
while the descriptions offer in-depth specifications for each functional
requirement, including actors, triggers, preconditions, and workflows.
This detailed analysis builds on the concise listings in Chapter 4,
creating a robust foundation for the technical design and development
phases of the project.

## 5.2 Use-Case Modeling

Use-case modeling is a technique used to identify, clarify, and organize
system requirements. It provides a way to describe the interactions
between a system and its users (actors) to achieve a specific goal. The
primary artifact of use-case modeling is the use-case diagram, which
offers a high-level, graphical representation of the system\'s
functionality and scope.

### ![](media/image13.png){width="7.475in" height="5.20625in"}5.2.1 Use-Case Diagram

[]{#_Toc201534998 .anchor}Figure 5.1: Use-Case Diagram for the Stock
Market Sentiment Dashboard

## 

## 5.3 Use-Case Descriptions

This section presents the detailed description and scenario tables for
each functional requirement (FR) identified in the system. Each
requirement is broken down into a formal use-case specification table,
illustrating its practical application and technical dependencies.

### 5.3.1 User Use-Case Descriptions

[]{#_Toc201534931 .anchor}Table 5.1: Use-Case for Viewing the Sentiment
Dashboard

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-01                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | View Sentiment Dashboard                             |
+--------------------+------------------------------------------------------+
| **Description**    | Users can view an interactive dashboard displaying   |
|                    | sentiment scores and stock prices for the curated    |
|                    | list of leading technology stocks (Top 20 IXT and    |
|                    | Magnificent Seven Combined).                         |
+--------------------+------------------------------------------------------+
| **Actors**         | User                                                 |
+--------------------+------------------------------------------------------+
| **Preconditions**  | The backend system has successfully fetched and      |
|                    | processed the latest data, and the web server is     |
|                    | running.                                             |
+--------------------+------------------------------------------------------+
| **Postconditions** | The dashboard is successfully rendered in the        |
|                    | user\'s browser with interactive data                |
|                    | visualizations.                                      |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The User opens their web browser and enters the  |
|                    | dashboard\'s URL.                                    |
|                    |                                                      |
|                    | 2\. The System retrieves the most recent sentiment   |
|                    | and price data from the data store.                  |
|                    |                                                      |
|                    | 3\. The System renders the main dashboard interface, |
|                    | displaying interactive charts for all monitored      |
|                    | stocks.                                              |
+--------------------+------------------------------------------------------+
| **Alternative      | \- If data fails to load, a message \"Unable to load |
| Flows**            | data. Please try again later.\" is displayed.        |
|                    |                                                      |
|                    | \- If no data is available, the dashboard shows a    |
|                    | warning message.                                     |
+--------------------+------------------------------------------------------+

[]{#_Toc201534932 .anchor}Table 5.2: Use-Case for Selecting a Time Range

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-02                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Select Time Range                                     |
+--------------------+-------------------------------------------------------+
| **Description**    | Allows the user to change the time window for         |
|                    | analysis (1-day, 7-day, 14-day) to observe            |
|                    | sentiment-price dynamics and dashboard sentiments     |
|                    | over different periods.                               |
+--------------------+-------------------------------------------------------+
| **Actors**         | User                                                  |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | The main dashboard is loaded and displayed.           |
+--------------------+-------------------------------------------------------+
| **Postconditions** | All visualizations and analytical tables on the       |
|                    | dashboard are updated to reflect the newly selected   |
|                    | time range.                                           |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. The user clicks on the \"14-Day\" button in the   |
|                    | time range selector.                                  |
|                    |                                                       |
|                    | 2\. The system filters the data for the last 14 days. |
|                    |                                                       |
|                    | 3\. The dashboard plots and correlation table update  |
|                    | accordingly.                                          |
+--------------------+-------------------------------------------------------+
| **Alternative      | If data for the selected range is incomplete, the     |
| Flows**            | dashboard displays a message indicating this.         |
+--------------------+-------------------------------------------------------+

[]{#_Toc201534933 .anchor}Table 5.3: Use-Case for Filtering by Stock

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-03                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Filter by Stock                                      |
+--------------------+------------------------------------------------------+
| **Description**    | Allows the user to isolate the data and              |
|                    | visualizations for a single, specific stock from the |
|                    | watchlist.                                           |
+--------------------+------------------------------------------------------+
| **Actors**         | User                                                 |
+--------------------+------------------------------------------------------+
| **Preconditions**  | The dashboard has loaded with data for all tracked   |
|                    | stocks.                                              |
+--------------------+------------------------------------------------------+
| **Postconditions** | The dashboard view is updated to display data        |
|                    | exclusively for the selected stock.                  |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The user opens the stock filter menu.            |
|                    |                                                      |
|                    | 2\. The user selects the stock symbol \"NVDA\".      |
|                    |                                                      |
|                    | 3\. The dashboard updates to show only the sentiment |
|                    | scores and price plots for NVDA.                     |
|                    |                                                      |
|                    | 4\. The correlation table adjusts to reflect data    |
|                    | for NVDA only.                                       |
+--------------------+------------------------------------------------------+
| **Alternative      | If the selected stock has no available data, a       |
| Flows**            | message like \"No data found for this stock\" is     |
|                    | displayed.                                           |
+--------------------+------------------------------------------------------+

[]{#_Toc201534934 .anchor}Table 5.4: Use-Case for Comparing Sentiment
vs. Stock Price

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-04                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Compare Sentiment vs. Stock Price                    |
+--------------------+------------------------------------------------------+
| **Description**    | Allows the user to view a dual axis plot that        |
|                    | overlays sentiment trends directly on top of stock   |
|                    | price movements for clear comparison.                |
+--------------------+------------------------------------------------------+
| **Actors**         | User                                                 |
+--------------------+------------------------------------------------------+
| Preconditions      | \- The user has selected a single stock (UC-03).     |
|                    |                                                      |
|                    | \- Sentiment and stock price data for the selected   |
|                    | stock and time range are available.                  |
+--------------------+------------------------------------------------------+
| **Postconditions** | A dual-axis chart comparing sentiment and price is   |
|                    | visible on the dashboard.                            |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. Upon selection of a stock, the System renders a  |
|                    | dual-axis chart by default.                          |
|                    |                                                      |
|                    | 2\. The chart displays stock price on the left       |
|                    | Y-axis and sentiment score on the right Y-axis; both |
|                    | plotted against a shared time-based X-axis.          |
+--------------------+------------------------------------------------------+
| **Alternative      | If either price or sentiment data is missing for the |
| Flows**            | selected period, the System does not render the plot |
|                    | and displays a warning.                              |
+--------------------+------------------------------------------------------+

[]{#_Toc201534935 .anchor}Table 5.5: Use-Case for Viewing Dynamic
Correlation Analysis

+-------------------+-------------------------------------------------------+
| **Aspect**        | **Details**                                           |
+===================+=======================================================+
| **Use Case ID**   | UC-05                                                 |
+-------------------+-------------------------------------------------------+
| **Use Case Name** | View Dynamic Correlation Analysis                     |
+-------------------+-------------------------------------------------------+
| **Description**   | Allows the user to view the dynamically calculated    |
|                   | Pearson correlation coefficient between sentiment and |
|                   | price for the selected context.                       |
+-------------------+-------------------------------------------------------+
| **Actors**        | User                                                  |
+-------------------+-------------------------------------------------------+
| **Preconditions** | A stock and time range are selected on the dashboard. |
+-------------------+-------------------------------------------------------+
| Postconditions    | The correlation value displayed on the dashboard      |
|                   | accurately reflects the currently visible data.       |
+-------------------+-------------------------------------------------------+
| **Main Flow**     | 1\. The User selects a stock and a time range.        |
|                   |                                                       |
|                   | 2\. The System automatically calculates the Pearson   |
|                   | correlation between the visible sentiment scores and  |
|                   | stock prices.                                         |
|                   |                                                       |
|                   | 3\. The System displays the calculated correlation    |
|                   | value (e.g., \"0.65\") in a dedicated section of the  |
|                   | dashboard.                                            |
+-------------------+-------------------------------------------------------+
| **Alternative     | If there is insufficient data (fewer than two data    |
| Flows**           | points) to compute a correlation, the System displays |
|                   | \"N/A\".                                              |
+-------------------+-------------------------------------------------------+

[]{#_Toc201534936 .anchor}Table 5.6: Use-Case for Evaluating Model
Accuracy

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-06                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Evaluate Model Accuracy                              |
+--------------------+------------------------------------------------------+
| **Description**    | Allows an administrator to review key performance    |
|                    | metrics for the sentiment analysis models.           |
+--------------------+------------------------------------------------------+
| **Actors**         | User (Administrator)                                 |
+--------------------+------------------------------------------------------+
| **Preconditions**  | A labelled dataset (ground truth) is available for   |
|                    | evaluation; The sentiment model has produced         |
|                    | predictions on this dataset                          |
+--------------------+------------------------------------------------------+
| **Postconditions** | Results are presented in a summary table or chart    |
|                    | for review                                           |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The user selects a sentiment model for           |
|                    | evaluation.                                          |
|                    |                                                      |
|                    | 2\. The system loads model predictions and the       |
|                    | ground truth labels.                                 |
|                    |                                                      |
|                    | 3\. It compares predictions against labels to        |
|                    | compute accuracy, precision, recall, and F1-score.   |
|                    |                                                      |
|                    | 4\. Results are displayed for review.                |
+--------------------+------------------------------------------------------+
| **Alternative      | If the labelled dataset or model predictions are     |
| Flows**            | unavailable, the system displays: "Evaluation cannot |
|                    | be completed. Check inputs."                         |
+--------------------+------------------------------------------------------+

[]{#_Toc199184028 .anchor}

Table 5.7: Use-Case for Configuring API Keys

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-07                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Configure API Keys                                   |
+--------------------+------------------------------------------------------+
| **Description**    | Allows an administrator to input or update API keys  |
|                    | for external data sources.                           |
+--------------------+------------------------------------------------------+
| **Actors**         | User (Administrator)                                 |
+--------------------+------------------------------------------------------+
| **Preconditions**  | Valid credentials for data source APIs are available |
+--------------------+------------------------------------------------------+
| **Postconditions** | API keys are stored securely and used in subsequent  |
|                    | API requests                                         |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The user opens the configuration or secure       |
|                    | environment.                                         |
|                    |                                                      |
|                    | 2\. The user enters new or existing API keys for     |
|                    | each service.                                        |
|                    |                                                      |
|                    | 3\. The system validates the format (optionally by   |
|                    | attempting a test connection).                       |
|                    |                                                      |
|                    | 4\. The keys are saved securely.                     |
|                    |                                                      |
|                    | 5\. A success message is displayed: "API keys        |
|                    | updated."                                            |
+--------------------+------------------------------------------------------+
| **Alternative      | \- If the key format is invalid, the system shows:   |
| Flows**            | "Invalid API key format."                            |
|                    |                                                      |
|                    | \- If saving fails, the system logs the error and    |
|                    | retains the previous keys.                           |
+--------------------+------------------------------------------------------+

> []{#_Toc201534938 .anchor}Table 5.8: Use-Case for Updating the Stock
> Watchlist

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-08                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Update Stock Watchlist                               |
+--------------------+------------------------------------------------------+
| **Description**    | Allows an administrator to add or remove stock       |
|                    | symbols from the list of stocks being monitored by   |
|                    | the system                                           |
+--------------------+------------------------------------------------------+
| **Actors**         | User (Administrator)                                 |
+--------------------+------------------------------------------------------+
| **Preconditions**  | User has access to the watchlist management.         |
+--------------------+------------------------------------------------------+
| **Postconditions** | The system uses the updated stock list in all        |
|                    | relevant modules                                     |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The user opens the watchlist editor.             |
|                    |                                                      |
|                    | 2\. The user adds "NVDA" and removes "TSLA".         |
|                    |                                                      |
|                    | 3\. The system updates the watchlist.                |
|                    |                                                      |
|                    | 4\. The dashboard now includes NVDA data.            |
+--------------------+------------------------------------------------------+
| **Alternative      | If "NVDA" is invalid, an error shows: "Invalid stock |
| Flows**            | symbol."                                             |
+--------------------+------------------------------------------------------+

[]{#_Toc199184032 .anchor}

Table 5.9: Use-Case for Managing Data Storage Settings

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-09                                                 |
+--------------------+-------------------------------------------------------+
| **Title**          | Manage Data Storage Settings                          |
+--------------------+-------------------------------------------------------+
| **Description**    | Allows an administrator to configure the data storage |
|                    | solution used by the application.                     |
+--------------------+-------------------------------------------------------+
| **Actors**         | User (Administrator)                                  |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | User has access to storage settings.                  |
+--------------------+-------------------------------------------------------+
| **Postconditions** | Data is saved to and retrieved from the selected      |
|                    | storage option                                        |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. The user opens the storage settings or config.    |
|                    |                                                       |
|                    | 2\. They select "SQLite" instead of local file        |
|                    | storage.                                              |
|                    |                                                       |
|                    | 3\. The system validates and saves the configuration. |
|                    |                                                       |
|                    | 4\. New data is now stored in SQLite.                 |
+--------------------+-------------------------------------------------------+
| **Alternative      | If connection details for the selected storage type   |
| Flows**            | are invalid or missing, the System displays an error  |
|                    | and reverts to the previous configuration.            |
+--------------------+-------------------------------------------------------+

[]{#_Toc201534940 .anchor}Table 5.10: Use-Case for Viewing System Logs

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-10                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | View System Logs                                      |
+--------------------+-------------------------------------------------------+
| **Description**    | Allows an administrator to access and view system     |
|                    | logs detailing application activity, errors, and      |
|                    | warnings for debugging and monitoring purposes.       |
+--------------------+-------------------------------------------------------+
| **Actors**         | User (Administrator)                                  |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | The system has been running and has generated log     |
|                    | entries.                                              |
+--------------------+-------------------------------------------------------+
| **Postconditions** | The user has reviewed the system logs to identify an  |
|                    | issue or confirm normal operation.                    |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. The User navigates to the \"System Logs\" viewer  |
|                    | panel.                                                |
|                    |                                                       |
|                    | 2\. The System displays a list of recent log entries, |
|                    | categorized and timestamped.                          |
|                    |                                                       |
|                    | 3\. The User applies a filter to show only \"ERROR\"  |
|                    | level logs from the last 24 hours.                    |
|                    |                                                       |
|                    | 4\. The System updates the view to show only the      |
|                    | relevant error logs.                                  |
+--------------------+-------------------------------------------------------+
| **Alternative      | If the log file cannot be loaded or is empty, the     |
| Flows**            | System displays a message such as \"Unable to         |
|                    | retrieve logs\".                                      |
+--------------------+-------------------------------------------------------+

### 5.3.2 System Use-Case Descriptions

[]{#_Toc201534941 .anchor}Table 5.11: Use-Case for Running the Data
Collection Pipeline

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-11                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Run the Data Collection Pipeline                      |
+--------------------+-------------------------------------------------------+
| **Description**    | The System fetches raw textual data (news, social     |
|                    | media posts) for the stocks in the watchlist from     |
|                    | multiple external APIs (Reddit, FinHub, NewsAPI,      |
|                    | Marketaux).                                           |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | 1\. Valid API keys for all data sources are           |
|                    | configured.                                           |
|                    |                                                       |
|                    | 2\. The stock watchlist is defined.                   |
|                    |                                                       |
|                    | 3\. The system has network connectivity.              |
+--------------------+-------------------------------------------------------+
| **Postconditions** | Raw, unstructured data from the APIs is successfully  |
|                    | saved to a temporary storage location, ready for      |
|                    | preprocessing.                                        |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. A trigger (manual or scheduled) initiates the     |
|                    | pipeline.                                             |
|                    |                                                       |
|                    | 2\. The System reads the stock watchlist and API      |
|                    | keys.                                                 |
|                    |                                                       |
|                    | 3\. For each stock, the System makes API calls to     |
|                    | each data source.                                     |
|                    |                                                       |
|                    | 4\. The System collects the returned textual data.    |
|                    |                                                       |
|                    | 5\. The System saves the raw data and logs the        |
|                    | operation\'s success.                                 |
+--------------------+-------------------------------------------------------+
| **Alternative      | If an API call for a specific source fails, the       |
| Flows**            | System logs the error, skips that source, and         |
|                    | continues with the next ones.                         |
+--------------------+-------------------------------------------------------+

[]{#_Toc199184038 .anchor}

Table 5.12: Use-Case for Preprocessing Raw Data

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-12                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Preprocess Raw Data                                   |
+--------------------+-------------------------------------------------------+
| **Description**    | The System cleans and normalizes the raw textual data |
|                    | to prepare it for sentiment analysis. This includes   |
|                    | tasks like removing duplicates, handling missing      |
|                    | values, and standardizing text.                       |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | Raw data has been collected and is available in       |
|                    | temporary storage.                                    |
+--------------------+-------------------------------------------------------+
| **Postconditions** | The data is cleaned, normalized, and ready for the    |
|                    | sentiment analysis models.                            |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. The System is triggered upon the completion of a  |
|                    | data collection run.                                  |
|                    |                                                       |
|                    | 2\. The System reads the raw data.                    |
|                    |                                                       |
|                    | 3\. The System performs cleaning operations:          |
|                    | lowercasing text, removing URLs, punctuation, and     |
|                    | stop words.                                           |
|                    |                                                       |
|                    | 4\. The System stores the cleaned, processed text for |
|                    | the next stage.                                       |
+--------------------+-------------------------------------------------------+
| **Alternative      | If a batch of data is found to be empty or corrupted, |
| Flows**            | the System logs a warning and skips that batch.       |
+--------------------+-------------------------------------------------------+

[]{#_Toc201534943 .anchor}Table 5.13: Use-Case for Performing Sentiment
Analysis

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-13                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Perform Sentiment Analysis                            |
+--------------------+-------------------------------------------------------+
| **Description**    | The System applies the appropriate NLP model (VADER   |
|                    | for Reddit, FinBERT for news) to the pre-processed    |
|                    | text to classify its sentiment as positive, negative, |
|                    | or neutral.                                           |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | Cleaned, pre-processed textual data is available.     |
+--------------------+-------------------------------------------------------+
| **Postconditions** | Each text entry is assigned a sentiment score and     |
|                    | label (positive, negative, neutral).                  |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. The System is triggered upon the completion of    |
|                    | data preprocessing.                                   |
|                    |                                                       |
|                    | 2\. The System identifies the source of the text, for |
|                    | example, Reddit or News.                              |
|                    |                                                       |
|                    | 3\. The System applies the FinBERT model to news      |
|                    | articles and the VADER model to Reddit posts.         |
|                    |                                                       |
|                    | 4\. The System generates a sentiment label and score  |
|                    | for each text entry.                                  |
+--------------------+-------------------------------------------------------+
| **Alternative      | If a sentiment model fails to load or process a       |
| Flows**            | batch, the System logs the error and skips that batch |
|                    | to avoid corrupting the results.                      |
+--------------------+-------------------------------------------------------+

[]{#_Toc199184042 .anchor}

Table 5.14: Use-Case for Storing Sentiment Results

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-14                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Store Sentiment Results                              |
+--------------------+------------------------------------------------------+
| **Description**    | The System saves the processed sentiment scores,     |
|                    | labels, and related metadata into a structured,      |
|                    | persistent data store.                               |
+--------------------+------------------------------------------------------+
| **Preconditions**  | Sentiment analysis has been performed on a batch of  |
|                    | data.                                                |
+--------------------+------------------------------------------------------+
| **Postconditions** | The sentiment data is permanently stored, indexed,   |
|                    | and accessible for retrieval by the dashboard.       |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The System receives the output from the          |
|                    | sentiment analysis models.                           |
|                    |                                                      |
|                    | 2\. The System formats the data into a structured    |
|                    | format (e.g., table rows).                           |
|                    |                                                      |
|                    | 3\. The System connects to the configured data store |
|                    | (per UC-09).                                         |
|                    |                                                      |
|                    | 4\. The System writes the new sentiment records to   |
|                    | the database.                                        |
+--------------------+------------------------------------------------------+
| **Alternative      | If the database writes operation fails, the System   |
| Flows**            | logs the error and can optionally save the data to a |
|                    | local fallback file.                                 |
+--------------------+------------------------------------------------------+

[]{#_Toc201534945 .anchor}Table 5.15: Use-Case for Scheduling Batch Data
Fetching

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-15                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Schedule Batch Data Fetching                         |
+--------------------+------------------------------------------------------+
| **Description**    | The system schedules data collection tasks to run at |
|                    | regular intervals.                                   |
+--------------------+------------------------------------------------------+
| **Preconditions**  | Scheduler is configured; API keys are set.           |
+--------------------+------------------------------------------------------+
| **Postconditions** | The system\'s data is periodically and automatically |
|                    | updated with the latest sentiment information.       |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. A system-level scheduler is configured to run at |
|                    | a specific time (e.g., 01:00 AM daily).              |
|                    |                                                      |
|                    | 2\. At the scheduled time, the scheduler triggers    |
|                    | the data collection pipeline (SY-FR1).               |
|                    |                                                      |
|                    | 3\. The pipeline executes and completes              |
+--------------------+------------------------------------------------------+
| **Alternative      | If the scheduler fails to trigger the job, a         |
| Flows**            | monitoring alert should be generated (as per         |
|                    | SY-FR10).                                            |
+--------------------+------------------------------------------------------+

[]{#_Toc201534946 .anchor}Table 5.16: Use-Case for Handling API Rate
Limits

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-16                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Handle API Rate Limits                               |
+--------------------+------------------------------------------------------+
| **Description**    | Manages API requests to ensure compliance with the   |
|                    | rate limits imposed by external data sources,        |
|                    | preventing service interruptions.                    |
+--------------------+------------------------------------------------------+
| **Preconditions**  | The data collection pipeline is actively making API  |
|                    | calls.                                               |
+--------------------+------------------------------------------------------+
| **Postconditions** | Data collection completes successfully without being |
|                    | blocked due to excessive requests.                   |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The System makes an API request.                 |
|                    |                                                      |
|                    | 2\. The external API returns a \"Rate Limit          |
|                    | Exceeded\" response.                                 |
|                    |                                                      |
|                    | 3\. The System reads the \"retry-after\" header to   |
|                    | determine the required waiting period.               |
|                    |                                                      |
|                    | 4\. The System pauses execution for that period and  |
|                    | then retries the request.                            |
+--------------------+------------------------------------------------------+
| **Alternative      | If an API has no \"retry-after\" header, the System  |
| Flows**            | waits for a default backoff period before retrying.  |
+--------------------+------------------------------------------------------+

[]{#_Toc201534947 .anchor}Table 5.17: Use-Case for Normalizing
Timestamps

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-17                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Normalize Timestamps                                  |
+--------------------+-------------------------------------------------------+
| **Description**    | Converts all timestamps from various data sources     |
|                    | into a single, standardized format to enable accurate |
|                    | data alignment and correlation analysis.              |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | Raw data containing timestamps in different formats   |
|                    | or time zones has been collected.                     |
+--------------------+-------------------------------------------------------+
| **Postconditions** | All data entries have a consistent, standardized      |
|                    | timestamp.                                            |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. During preprocessing (SY-FR2), the System         |
|                    | identifies the timestamp field for each data record.  |
|                    |                                                       |
|                    | 2\. The System parses the timestamp string.           |
|                    |                                                       |
|                    | 3\. The System converts the timestamp to the UTC time |
|                    | zone and formats it as an ISO 8601 string.            |
|                    |                                                       |
|                    | 4\. The original timestamp is replaced with the       |
|                    | standardized one.                                     |
+--------------------+-------------------------------------------------------+
| **Alternative      | If a timestamp is invalid or cannot be parsed, the    |
| Flows**            | System logs a warning and discards the affected data  |
|                    | row.                                                  |
+--------------------+-------------------------------------------------------+

[]{#_Toc201534948 .anchor}Table 5.18: Use-Case for Triggering
Visualization Updates

+--------------------+------------------------------------------------------+
| **Aspect**         | **Details**                                          |
+====================+======================================================+
| **Use Case ID**    | UC-18                                                |
+--------------------+------------------------------------------------------+
| **Use Case Name**  | Trigger Visualization Updates                        |
+--------------------+------------------------------------------------------+
| **Description**    | Automatically refreshes the data presented on the    |
|                    | dashboard when new sentiment and price data becomes  |
|                    | available in the data store.                         |
+--------------------+------------------------------------------------------+
| **Preconditions**  | New data has been successfully written to the data   |
|                    | store.                                               |
+--------------------+------------------------------------------------------+
| **Postconditions** | The dashboard reflects the most recent data.         |
+--------------------+------------------------------------------------------+
| **Main Flow**      | 1\. The dashboard application is configured to poll  |
|                    | the data store for changes at a regular interval.    |
|                    |                                                      |
|                    | 2\. The System detects that new data has been added  |
|                    | since the last check.                                |
|                    |                                                      |
|                    | 3\. The System automatically re-queries the data and |
|                    | refreshes all plots and tables.                      |
+--------------------+------------------------------------------------------+
| **Alternative      | If the data query fails during a refresh attempt,    |
| Flows**            | the dashboard continues to show the last known good  |
|                    | data and logs an error.                              |
+--------------------+------------------------------------------------------+

[]{#_Toc201534949 .anchor}Table 5.19: Use-Case for Logging Pipeline
Operations

+--------------------+-------------------------------------------------------+
| **Aspect**         | **Details**                                           |
+====================+=======================================================+
| **Use Case ID**    | UC-19                                                 |
+--------------------+-------------------------------------------------------+
| **Use Case Name**  | Log Pipeline Operations                               |
+--------------------+-------------------------------------------------------+
| **Description**    | The System records all significant activities,        |
|                    | successes, and failures that occur within the data    |
|                    | pipeline for monitoring and debugging purposes.       |
+--------------------+-------------------------------------------------------+
| **Preconditions**  | The pipeline is actively performing tasks             |
+--------------------+-------------------------------------------------------+
| **Postconditions** | A comprehensive, structured log of system activities  |
|                    | is available for review.                              |
+--------------------+-------------------------------------------------------+
| **Main Flow**      | 1\. A pipeline task such as data collection begins.   |
|                    |                                                       |
|                    | 2\. The System writes a log entry: \"INFO: Data       |
|                    | collection started.\"                                 |
|                    |                                                       |
|                    | 3\. The task completes successfully.                  |
|                    |                                                       |
|                    | 4\. The System writes another log entry: \"INFO: Data |
|                    | collection completed successfully. 500 records        |
|                    | fetched.\"                                            |
+--------------------+-------------------------------------------------------+
| **Alternative      | If a task fails, the System writes a descriptive      |
| Flows**            | error log: \"ERROR: Failed to connect to FinHub API.  |
|                    | Connection timed out.\"                               |
+--------------------+-------------------------------------------------------+

## 5.4 Dynamic Model

Use Case diagrams offer an overview of interactions between users and
systems, whereas dynamic models explore the system\'s behavior over time
and the order of operations. This segment showcases different UML
dynamic models, such as Sequence Diagrams, Activity Diagrams, and State
Diagrams, to demonstrate the flow of control, interactions among
objects, and transitions of states in essential processes of the
dashboard. These models play an essential role in comprehending the
system\'s behavior during execution and verifying that the interactions
created meet the defined functional criteria.

### 5.4.1 Activity Diagram

![[]{#_Toc199184358 .anchor}Figure 5.2: User Dashboard Interaction
Diagram](media/image14.png){width="3.2348403324584427in"
height="4.108333333333333in"}

The activity diagram in Figure 5.2 illustrates the interaction flow
between the user and the Stock Market Sentiment Dashboard from the
moment the dashboard is accessed. Initially, the system loads the
interface and attempts to fetch the latest sentiment and price data. If
data is available, the default dashboard view is displayed; otherwise,
the user is informed with a \"No Data Available\" message. Once the
dashboard is active, the system enters a wait state for user
interaction. The user can then select a stock symbol and a preferred
time range (1-day, 7-day, or 14-day), prompting the system to filter the
relevant data accordingly.

Following the data filtering, the dashboard updates a dual-axis chart to
visualize sentiment scores alongside stock price movements. It then
attempts to calculate the Pearson correlation between sentiment and
price. If the correlation is computable, the value is displayed; if not,
\"N/A\" is shown. The user may subsequently change the selection, which
loops the flow back to data filtering, enabling real-time interactivity.
This diagram effectively captures the dashboard's core functionality and
dynamic responsiveness, emphasizing its user-centric design and
analytical features.

![[]{#_Toc199184353 .anchor}Figure 5.3: Data Collection Activity
Diagram](media/image15.png){width="5.620833333333334in"
height="3.243812335958005in"}

Figure 5.3 presents the Data Collection Activity Diagram, detailing the
backend workflow for retrieving sentiment-related data. The process
begins with a scheduled or manual trigger, followed by loading critical
configurations such as API keys and the stock watchlist. Once internet
connectivity is verified, the system iterates through each stock symbol
in the watchlist and initiates API requests to four distinct data
sources: Reddit (via PRAW), FinHub, Marketaux, and NewsAPI. For each
source, the system incorporates logic to handle API rate limits by
checking responses and applying a \"wait and retry\" mechanism when
necessary, ensuring stable and compliant data collection.

After fetching data from all sources, the system logs any encountered
API errors or failures for monitoring purposes. Regardless of the
outcome, successfully retrieved raw data is stored temporarily in
preparation for preprocessing. In the case of no network connectivity,
the system exits early and logs a corresponding message. This diagram
effectively visualizes the fault-tolerant and modular nature of the data
ingestion pipeline, ensuring robustness and scalability in acquiring
timely financial and sentiment data across multiple APIs.

![[]{#_Toc199184354 .anchor}Figure 5.4: Preprocessing Activity
Diagram](media/image16.png){width="3.995833333333333in"
height="3.9337510936132984in"}

The Preprocessing Activity Diagram in Figure 5.4 describes the data
cleaning pipeline that is launched once the period of successful data
reception starts. It starts with the loading of raw textual data in the
temporary storage. In case of unavailable valid raw data, the system
logs a warning and stops further operations. Other than this, it also
goes through the data and cleans it systematically in a number of steps,
including eliminating duplicates, discarding URLs, emojis, and other
special characters, normalizing all the text to the lowercase format,
and ending up with stopwords and otherwise un-relevant tokens. The steps
will reduce noise levels and normalize the text to be analyzed for
sentiment.

It then converts all timestamps into the UTC ISO format so that the
temporal consistency of data sources is maintained. Depending on which
source the text finds its origin whether it is Reddit or APIs of
financial news, system labels it as such. It is vital in terms of
guiding the related sentiment model (VADER or FinBERT) later on. After
the preprocessing, the cleaned text and the corresponding metadata are
deposited on a precleaned storage layer that is ready to get classified
as sentiment. This diagram implies that it is crucial to perform the
preprocessing in a semi-structured or at least domain-aware manner to
ensure high-quality and reliability of the downstream analysis.

![[]{#_Toc199184355 .anchor}Figure 5.5: Sentiment Analysis Activity
Diagram](media/image17.png){width="5.420833333333333in"
height="3.3966469816272964in"}

Sentiment Analysis Activity Diagram described in figure 5.5 shows the
automatic process of sentiment labeling and scoring of the preprocessed
data in the textual form. This is enabled when the clean text entries
are loaded by the storage after which preprocessing is carried out. In
case no data is there, the system records a warning and quits.
Otherwise, it runs through all entries and verifies the source: when the
text appeared on Reddit, the VADER model will be used; otherwise, the
FinBERT model is taken. All the models label the sentiment to be
Positive, Neutral or Negative and create a sentiment score.

Having been classified, the system attaches important metadata to every
record such as the score on the basis of sentiment, label, time stamp,
the source and the stock symbol upon which it is corresponding to. Such
augmented findings will then be stored in organized storage thus they
are easily searched to be either re-analysed or visualised on dashboard.
This diagram is an effective representation of how domain-specific NLP
models need to be tailored to application according to data source,
achieving accurate and context-sensitive sentiment classification in a
wide variety of financial content.

![[]{#_Toc199184356 .anchor}Figure 5.6: Storage Module Activity
Diagram](media/image18.png){width="5.096415135608049in"
height="3.0125in"}

The Storage Module Activity Diagram is shown in Figure 5.6, which
captures the last state of the data pipeline storing the sentiment
analysis results. The module is also triggered as soon as sentiment
scoring is completed and it starts by loading all available data based
on their output such as score, label, timestamp, source and stock
symbol. The system subsequently verifies the selected type of storage
that may either include one of the three: a SQLite database, a local
file, or a cloud storage. With this arrangement, the system will create
proper connection and add or insert new sentiment record
correspondingly.

As soon as the write operation has been completed, the system verifies
that it has been done successfully. In order to successfully do so, it
records a confirmation message and else records an error and applies an
alternate mechanism like backing up to a local backup file to avoid
running out of data. This diagram emphasizes the fault-tolerant and
flexible storage architecture of the system which accommodates multiple
backends and makes data persistent by employing fallback protocols when
collision occurs.

## 5.5 State Diagrams

![[]{#_Toc199184359 .anchor}Figure 5.7: Data Collection State
Diagram](media/image19.png){width="3.5402919947506564in"
height="5.3625in"}

Figure 5.7 illustrates the Data Collection State Diagram, which
represents the various operational states of the sentiment data
acquisition process within the system. The workflow begins in the
Scheduled state after a job is registered, either manually by a user or
automatically by a system scheduler. When the scheduled time arrives,
the system transitions to the Running state, initiating the data
retrieval process by querying external APIs such as Reddit, NewsAPI, and
others, represented by the Collecting state.

If API rate limits are encountered, the system enters the RateLimited
state and proceeds to Retrying using a backoff strategy. A successful
retry leads to the Collected state, while exhausted retries or critical
issues such as missing configurations or widespread API failures move
the system to the Failed state. Once all data is either collected or a
failure is handled, the system moves to Completed, where it logs
outcomes via Logged. This state diagram emphasizes the system's
resilience and its ability to gracefully handle failures and retry
mechanisms during the data collection lifecycle.

![[]{#_Toc201535005 .anchor}Figure 5.8: Sentiment Record State
Diagram](media/image20.png){width="2.6958333333333333in"
height="4.700426509186352in"}

Figure 5.8 shows the Sentiment Record State Diagram, which describes the
lifecycle of one single data record of sentiment, as collected and
logged. This starts with uncleaned text obtained via an external API and
enters the Cleaned state after processing by text preprocessing, which
eliminates noise including stopwords, URLs, emoji, and so on. The data
would then be sent to the Normalized state; the timestamps here will be
normalized into ISO UTC format so that all record timestamps are
consistent.

Then, the cleaned and normalized text is run in a sentiment analysis
model (VADER or FinBERT), going into the Scored state. Provided that the
output is valid, the record is swapped to Stored and is designated as
Loggable and is finally forwarded to the logging system with an
informational (INFO) status. In contrast, when the sentiment score is
invalid or the parsing process throws an error, the record will be
Discarded and logged either with a Warning status or an Error status. In
this state diagram, there is a focus on the system to support data
integrity, traceability, and resilient error handling within the
sentiment analysis pipeline.

![[]{#_Toc201535006 .anchor}Figure 5.9: Pipeline State
Diagram](media/image21.png){width="5.479166666666667in"
height="4.685925196850394in"}

Figure 5.9 illustrates the Pipeline State Diagram, which provides a
high-level view of the sequential stages in the full sentiment analysis
pipeline. The process begins in the Idle state, where the system awaits
a scheduled or manual trigger. Upon activation, it enters the
Initialized state to load API keys and configuration files, then
transitions into Collecting to fetch raw data from external sources
(UC-11). If data retrieval is successful, the system proceeds with
Preprocessing (UC-12) to clean and normalize text before applying
sentiment models in the Scoring state (UC-13).

From there, results are handled in the Saving State (UC-14), where
sentimental data is stored in the configured backend. Depending on the
outcome, the pipeline may reach one of three end states: Completed (all
data successfully stored), PartialSuccess (some records saved, others
failed), or Failed (critical errors in any stage, including fetch,
processing, or storage). Regardless of success level, all outcomes are
recorded in the Logged state for traceability. This state diagram
clearly captures the linear yet fault-tolerant nature of the pipeline,
highlighting recovery paths and error-handling mechanisms embedded at
each stage.

## 5.6 Sequence Diagram

This section outlines the sequence diagrams for the project, detailing
the interaction flows between components for both user and system-level
processes. It includes user-facing interactions such as viewing
dashboards, filtering data, and managing settings, as well as system
operations like data collection, preprocessing, sentiment analysis, and
error monitoring, providing a comprehensive view of the system\'s
dynamic behavior.

The following sequence diagram (Figure 5.10) models the function
requirement (U-FR1) which is explained in table (5.1). 

![[]{#_Toc199184366 .anchor}Figure 5.10: View Sentiment Dashboard
Sequence Diagram](media/image22.png){width="3.9875in"
height="3.228915135608049in"}

Figure 5.10 illustrates the View Sentiment Dashboard Sequence Diagram,
which models the interaction between the user, dashboard interface,
backend server, and data layer in fulfilling the functional requirement
(U-FR1). The sequence begins when the user opens the dashboard,
prompting the UI to send a request to the backend for the initial data.
The backend queries the data layer for the latest sentiment scores and
stock prices, and upon successful retrieval, returns the cleaned data in
JSON format to the frontend. The dashboard then renders interactive
charts based on this data, enabling the user to begin exploring
sentiment trends visually.

The diagram also includes an alternate flow to handle cases where no
data is available. In such scenarios, the backend responds with an error
message, and the dashboard UI displays a "No Data Available" notice to
inform the user. Additionally, optional error handling is shown if the
server encounters a failure, the UI will display an error banner, while
the backend logs the issue for diagnostics. This sequence diagram
clearly demonstrates how the system prioritizes both responsiveness and
user feedback, ensuring a smooth user experience even in the face of
backend issues or data unavailability.

The following sequence diagram (Figure 5.11) models the function
requirement (U-FR2) which is explained in table (5.2). 

![[]{#_Toc199184367 .anchor}Figure 5.11: Select Time Range Sequence
Diagram](media/image23.png){width="5.429166666666666in"
height="3.1938527996500437in"}

Figure 5.11 illustrates the Select Time Range Sequence Diagram, which
models the process initiated when a user selects a new timeframe from
the time range dropdown in the dashboard, fulfilling functional
requirement U-FR2. The sequence begins with the dashboard UI sending a
request to the backend server to retrieve data specific to the selected
time range. The backend then queries the data layer for corresponding
sentiment scores and stock price information, filtering results based on
the user\'s chosen timeframe.

If relevant data exists for the selected period, the backend returns it
in JSON format, allowing the dashboard to update the charts and
correlation table accordingly. In cases where data is partially
available or missing entirely, a warning or fallback is triggered. The
dashboard will notify the user with a message such as "Data Incomplete
for Selected Range," ensuring transparency. This sequence highlights the
system\'s responsiveness to user interactions and its ability to
dynamically adapt visualizations based on filtered time-based queries,
while also accounting for incomplete data scenarios.

The following sequence diagram (Figure 5.12) models the function
requirement (U-FR3) which is explained in table (5.3). 

![[]{#_Toc199184368 .anchor}Figure 5.12: Filter by Stock Sequence
Diagram](media/image24.png){width="5.304166666666666in"
height="3.1997550306211724in"}

Figure 5.12 illustrates the Filter by Stock Sequence Diagram, which
models the interaction triggered when a user selects a specific stock
from the dropdown menu, in line with functional requirement U-FR3. Upon
selection, the dashboard UI sends a request to the backend server for
sentiment and price data related to the selected stock. The backend
queries the data layer and returns a filtered dataset corresponding to
that specific stock symbol.

If the data is successfully retrieved, it is sent back to the dashboard
UI, which then updates all relevant visualizations such as sentiment
charts and correlation metrics to reflect only the selected stock. If no
data is available for the chosen stock, the backend sends a warning
message, and the UI displays an appropriate notification like "No Data
for Selected Stock." This sequence highlights the dashboard's
flexibility and near real-time responsiveness in delivering
stock-specific insights, while also ensuring graceful handling of data
unavailability.

The following sequence diagram (Figure 5.13) models the function
requirement (U-FR4) which is explained in table (5.4). 

![[]{#_Toc199184369 .anchor}Figure 5.13: Compare Sentiment vs. Stock
Price Sequence Diagram](media/image25.png){width="4.870833333333334in"
height="3.234590988626422in"}

Figure 5.13 illustrates the Compare Sentiment vs. Stock Price Sequence
Diagram, modeling the backend and frontend interactions that occur once
a user selects both a stock and a time range fulfilling functional
requirement U-FR4. This process is initiated when the dashboard UI sends
a request to the backend to fetch sentiment and stock price data for the
specified parameters. The backend server queries the data layer and
returns a merged dataset where sentiment scores and price values are
time-aligned.

If the data is complete and properly synchronized, the dashboard renders
a dual-axis chart sentiment plotted on one Y-axis and stock price on the
other, both mapped to a common X-axis representing time. This allows
users to visually interpret the relationship between sentiment trends
and price movements over the selected period. If the dataset is
incomplete or misaligned, the system triggers a warning message, such as
"Missing sentiment or price values," ensuring transparency. This diagram
highlights the importance of time-series synchronization and emphasizes
the system's ability to provide intuitive, comparative visual analytics.

The following sequence diagram (Figure 5.14) models the function
requirement (U-FR5) which is explained in table (5.5). 

![[]{#_Toc199184370 .anchor}Figure 5.14: View Dynamic Correlation
Analysis Sequence
Diagram](media/image26.png){width="4.179166666666666in"
height="3.3338757655293088in"}

Figure 5.14 illustrates the View Dynamic Correlation Analysis Sequence
Diagram, which models the backend-driven computation and frontend
display of the Pearson correlation between sentiment scores and stock
prices aligned with functional requirement U-FR5. This process is
triggered after the user selects both a stock and a time range. The
dashboard UI sends a request to the backend server, which queries the
data layer for time-aligned sentiment and price series. Once retrieved,
the backend computes the Pearson correlation coefficient.

If the dataset contains at least two valid data points, the backend
returns the correlation value, which the dashboard UI displays
numerically. In cases where there is insufficient data (fewer than two
matched records), the system instead returns "N/A" and shows a message
such as "Correlation Not Available." This diagram effectively captures
the reactive nature of the dashboard's analytics engine, ensuring
correlation metrics are automatically updated whenever filters are
changed thereby providing users with near real-time, interpretable
statistical insights into sentiment-price relationships.

The following sequence diagram (Figure 5.15) models the function
requirement (U-FR6) which is explained in table (5.6). 

![[]{#_Toc199184371 .anchor}Figure 5.15: Evaluate Model Accuracy
Sequence Diagram](media/image27.png){width="5.004166666666666in"
height="3.4186876640419945in"}

Figure 5.15 illustrates the Evaluate Model Accuracy Sequence Diagram,
which models the evaluation process of a sentiment analysis model as
triggered by the user, fulfilling functional requirement U-FR6. Upon
initiating the evaluation from the dashboard UI, a request is sent to
the backend server, which delegates the task to the Model Evaluation
Engine. The engine fetches the model's predictions along with ground
truth labels from the data layer, then proceeds to compute key
performance metrics such as Accuracy, Precision, Recall, and F1-score.

If the evaluation is successful, the computed metrics are returned to
the backend server, which in turn sends them to the dashboard for
display in either a table or chart format. However, if an error occurs
such as missing labels or inconsistent data, the system returns a
failure message and displays a warning or error dialog to inform the
user. This diagram encapsulates the modular and testable design of the
system, emphasizing support for model transparency and performance
validation directly within the user interface.

The following sequence diagram (Figure 5.16) models the function
requirement (U-FR7) which is explained in table (5.7). 

![[]{#_Toc199184372 .anchor}Figure 5.16: Configure API Keys Sequence
Diagram](media/image28.png){width="4.7875in"
height="3.195048118985127in"}

Figure 5.16 illustrates the Configure API Keys Sequence Diagram, which
models the secure process of submitting and storing external API keys
aligned with functional requirement U-FR7. The sequence begins when the
user accesses the API configuration panel via the dashboard UI and
enters a new API key. The key is then submitted to the backend server
using a secure POST request. The server validates the format of the
submitted key to ensure it adheres to expected patterns.

If the key format is valid, the backend proceeds to encrypt the key and
securely store it in a designated storage module, returning a success
message to the user. If the format is invalid, the user is notified with
an appropriate error message. A key design highlight in this sequence is
the secure handling of sensitive data, ensuring API keys are never
exposed in plain text and are always encrypted at rest. This diagram
reinforces the system's commitment to maintaining security and user
control over third-party integrations.

The following sequence diagram (Figure 5.17) models the function
requirement (U-FR8) which is explained in table (5.8). 

![[]{#_Toc199184373 .anchor}Figure 5.17: Update Stock Watchlist Sequence
Diagram](media/image29.png){width="5.3375in"
height="3.7166491688538934in"}

Figure 5.17 illustrates the Update Stock Watchlist Sequence Diagram,
modeling the flow for modifying the user's list of tracked stocks
fulfilling functional requirement U-FR8. The sequence begins when the
user opens the Watchlist Manager in the dashboard UI and submits a
modified list. The updated watchlist is sent to the backend server,
which validates all the stock symbols provided against a predefined list
or external API to ensure accuracy and existence.

If all stock symbols are valid, the server overwrites the previously
stored watchlist in the data layer and returns a success confirmation to
the UI. Conversely, if one or more symbols are invalid or unrecognized,
an error message is returned such as Invalid Stock Symbol, prompting the
user to correct their input. The updated watchlist directly influences
both the backend data pipeline and the dashboard's filtering mechanisms,
ensuring that all data collection and visualization components remain
aligned with the user's preferences. This diagram demonstrates a secure
and user-controlled mechanism for customizing data scope in a flexible
yet validated environment.

The following sequence diagram (Figure 5.18) models the function
requirement (U-FR9) which is explained in table (5.9). 

![[]{#_Toc199184374 .anchor}Figure 5.18: Manage Data Storage Sequence
Diagram](media/image30.png){width="4.895833333333333in"
height="3.115216535433071in"}

Figure 5.18 illustrates the Manage Data Storage Sequence Diagram, which
models the process of configuring the storage backend for the
application fulfilling functional requirement U-FR9. The interaction
begins when the user opens the storage settings panel on the dashboard
and selects a preferred backend option. This configuration is submitted
to the backend server, which forwards it to the Storage Manager
component responsible for applying and validating the new settings.

If the connection to the chosen storage backend is successful, the
system confirms the configuration and notifies the user with a message
like "Storage Updated Successfully." In case of a connection failure or
misconfiguration, an appropriate error message such as "Failed to
Connect to Storage" is returned and shown in the dashboard. This
sequence ensures that storage settings are applied securely and
transparently, with immediate feedback, while also emphasizing that
these configurations directly influence how future data read/write
operations will be handled within the system.

The following sequence diagram (Figure 5.19) models the function
requirement (U-FR10) which is explained in table (5.10). 

![[]{#_Toc199184375 .anchor}Figure 5.19: View System Logs Sequence
Diagram](media/image31.png){width="5.645833333333333in"
height="3.1219542869641295in"}

Figure 5.19 illustrates the View System Logs Sequence Diagram, which
models the interaction flow for accessing and filtering operational logs
aligned with functional requirement U-FR10. The process begins when the
user navigates to the \"System Logs\" panel in the dashboard UI and
applies a filter. This triggers a request to the backend server, which
then queries the log storage for entries that match the specified filter
criteria.

If matching logs are found, the backend returns them to the dashboard,
where they are displayed in a viewer containing timestamps, severity
levels, and message details. If no logs match the filter, the UI instead
displays a message such as "No Logs Available for This Filter." This
sequence diagram underscores the system's support for operational
transparency, allowing users to audit activities such as API failures,
system alerts, or pipeline events through a structured, user-friendly
interface.

The following sequence diagram (Figure 5.20) models the function
requirement (SY-FR1) which is explained in table (5.11). 

![[]{#_Toc199184376 .anchor}Figure 5.20: Data Collection Pipeline
Sequence Diagram](media/image32.png){width="5.020833333333333in"
height="3.6324704724409447in"}

Figure 5.20 illustrates the Data Collection Pipeline Sequence Diagram,
which models the end-to-end execution flow for gathering raw
sentiment-related data from multiple external APIs. This interaction
supports functional requirement SY-FR1, focusing on initiating,
coordinating, and validating the data collection process. The sequence
can be initiated either manually by the user or automatically through a
scheduler, which then triggers the pipeline and loads the necessary API
keys and stock watchlist configurations.

Once the setup is complete, the pipeline proceeds to interact with
various APIs such as Reddit, FinHub, Marketaux, and NewsAPI via the API
Manager. Each service is queried independently to fetch relevant data.
The results are returned asynchronously and passed to the data layer,
where all raw text and metadata are aggregated and stored in a central
raw data batch. If all sources respond successfully, the system confirms
that the data collection has been completed and displays a successful
message.

In cases where one or more APIs fail (due to rate limits, downtime, or
invalid credentials), the pipeline still proceeds to log the error, save
any partial results, and notify the user with a warning. This ensures
robustness and transparency, preventing a single-point failure from
halting the pipeline. The sequence concludes by logging into each key
event both successful and failed to maintain full traceability of the
batch collection operation. This diagram effectively captures the
complexity and resilience of the system's multi-source ingestion
framework.

The following sequence diagram (Figure 5.21) models the function
requirement (SY-FR2) which is explained in table (5.12). 

![[]{#_Toc199184377 .anchor}Figure 5.21: Preprocess Raw Data Sequence
Diagram](media/image33.png){width="5.02278324584427in"
height="3.1365748031496063in"}

Figure 5.21 illustrates the Preprocess Raw Data Sequence Diagram, which
models the step-by-step data cleaning and standardization process prior
to sentiment analysis, in alignment with functional requirement SY-FR2.
The sequence begins when the Pipeline Controller triggers the
preprocessing task, prompting the Preprocessing Engine to request a
batch of raw data records from the Data Layer. If raw data is available,
it is returned and passed sequentially through a series of specialized
components for cleaning and enrichment.

The Cleaner removes URLs, emojis, noise characters, and stopwords from
the text, resulting in a cleaned version of the dataset. The Timestamp
Normalizer then standardizes all timestamps to the ISO UTC format,
ensuring consistency across sources and facilitating temporal alignment.
After normalization, the Source Tagger classifies each record as either
"Reddit" or "News" based on its origin. The preprocessed records now
cleaned, time-aligned, and tagged are saved back into the data layer,
and the preprocessing engine confirms task completion.

If no raw data is available, the engine aborts the process and logs a
message such as "No Data to Process," preventing unnecessary execution.
Once the cleaned dataset is confirmed, it is marked as ready for
downstream sentiment classification. This sequence demonstrates the
system\'s modular and fault-tolerant design, ensuring high-quality data
enters the sentiment pipeline while maintaining traceability and
operational integrity.

The following sequence diagram (Figure 5.22) models the function
requirement (SY-FR3) which is explained in table (5.13). 

![[]{#_Toc199184378 .anchor}Figure 5.22: Perform Sentiment Analysis
Sequence Diagram](media/image34.png){width="5.479166666666667in"
height="3.494798775153106in"}

Figure 5.22 illustrates the Perform Sentiment Analysis Sequence Diagram,
which outlines the system-level interaction for processing preprocessed
text using sentiment models, in accordance with functional requirement
SY-FR3. The process begins when the Pipeline Controller triggers the
sentiment analysis phase. The Sentiment Engine requests preprocessed,
tagged data from the Data Layer, which includes cleaned text entries
labeled by their content source.

Once the data is retrieved, it is routed by the Model Router based on
the source tag. If the source is Reddit, the text is passed to the VADER
Model for sentiment analysis; if the source is News, it is analyzed
using FinBERT. Each model returns a sentiment label (positive, neutral,
or negative) along with a numerical score representing the sentiment
intensity. The engine then compiles all sentiment results and saves them
to the data layer, where they are confirmed and marked for downstream
use, such as visualization or statistical correlation.

If no preprocessed data is available, the engine aborts the task and
logs a warning such as "No Data Available," avoiding unnecessary
computation. The final output from this process includes labeled and
scored sentiment records, which are stored for both dashboard display
and further analysis. This diagram clearly reflects the system's
modular, source-aware design and its ability to dynamically switch
between sentiment models based on content origin, thereby optimizing
contextual relevance and accuracy.

The following sequence diagram (Figure 5.23) models the function
requirement (SY-FR4) which is explained in table (5.14). 

![[]{#_Toc199184379 .anchor}Figure 5.23: Store Sentiment Results
Sequence Diagram](media/image35.png){width="5.571759623797026in"
height="3.2666119860017497in"}

Figure 5.23 illustrates the Store Sentiment Results Sequence Diagram,
modeling the final step in the sentiment analysis pipeline: storing
analysis results aligned with functional requirement SY-FR4. This
process is initiated by the Sentiment Engine, which begins by sending
the batch of results to the Data Validator for format and type checking.
Validation ensures that each record contains the required attributes
such as score, label, timestamp, stock symbol, and source in the correct
structure.

If all records are valid, the system enters a loop where each sentiment
record is written individually by the Storage Manager. After each write
operation, the result is evaluated: a successful write is confirmed,
while any failure triggers an error response and is logged by the Log
System. Once all records are processed, a summary of the operation
highlighting the number of successful and failed entries is logged for
traceability. Conversely, if the initial validation fails, the system
skips the write phase entirely, returning validation errors and logging
the failure.

This sequence emphasizes data integrity, fault isolation, and audit
readiness. By validating records upfront and confirming each write
individually, the system ensures only clean and accurate data enters
storage. Furthermore, granular logging at both the record and batch
level supports troubleshooting and performance monitoring.

The following sequence diagram (Figure 5.24) models the function
requirement (SY-FR5) which is explained in table (5.15). 

![[]{#_Toc199184380 .anchor}Figure 5.24: Schedule Batch Data Fetching
Sequence Diagram](media/image36.png){width="5.254166666666666in"
height="3.1101399825021874in"}

Figure 5.24 illustrates the Schedule Batch Data Fetching Sequence
Diagram, which models the automated scheduling and execution of data
collection, fulfilling system-level functional requirement SY-FR5. The
process is initiated when the user configures a schedule. At the
designated time, the System Scheduler triggers the Pipeline Controller,
which initiates the data collection sequence.

The Data Collection Module then proceeds to load API keys and the stock
watchlist, after which it sends requests to external APIs such as
Reddit, NewsAPI, and FinHub. The response whether complete or partial is
then returned to the system. If the data collection is successful, the
system logs an informational message indicating that the task was
completed. If the collection fails (due to rate limits, service outages,
or invalid keys), the error is logged, and an optional failure
notification may be sent to alert the user or system administrator.

This diagram emphasizes the system's ability to automate recurring tasks
while maintaining operational awareness through detailed logging. By
decoupling schedule management from execution logic, the system ensures
flexibility, reliability, and maintainability for large-scale or
long-term sentiment monitoring operations.

The following sequence diagram (Figure 5.25) models the function
requirement (SY-FR6) which is explained in table (5.16). 

![[]{#_Toc199184381 .anchor}Figure 5.25: Handle API Rate Limits Sequence
Diagram](media/image37.png){width="5.682870734908136in"
height="3.669350393700787in"}

Figure 5.25 illustrates the Handle API Rate Limits Sequence Diagram,
which captures the logic used to manage rate-limiting responses from
external APIs during data collection, addressing system functional
requirement SY-FR6. The process begins when a user (or scheduler)
triggers a data collection task. The Data Collection Module initiates an
API request to an external service. If the request is successful, the
response data is returned, and the system continues its normal flow.

However, if the API returns an HTTP 429 response (indicating the rate
limit has been exceeded), the request is passed to the Rate Limit
Handler. The handler first checks whether the Retry-After header is
present in the response. If it is, the system waits for the specified
duration before retrying the request. If the header is not provided, a
default backoff duration is used to avoid further violation. After the
wait, the system retries the API call. Whether the second attempt
returns data or fails again, the event is logged via the Log System for
monitoring purposes.

This diagram highlights the system\'s resilience against rate-limiting
scenarios by implementing smart retry mechanisms. It also ensures that
external API usage complies with rate policies, prevents cascading
failures, and provides observability through structured logging key
qualities for a robust, production-ready data ingestion system.

The following sequence diagram (Figure 5.26) models the function
requirement (SY-FR7) which is explained in table (5.17). 

![[]{#_Toc199184382 .anchor}Figure 5.26: Normalize Timestamps Sequence
Diagram](media/image38.png){width="3.995833333333333in"
height="3.2988199912510936in"}

Figure 5.26 illustrates the Normalize Timestamps Sequence Diagram, which
models the timestamp standardization process during data preprocessing,
addressing system requirement SY-FR7. The flow begins when the
Preprocessing Module initiates the task and instructs the Timestamp
Normalizer to begin normalization. The Data Layer returns a batch of raw
data records containing diverse timestamp formats from various sources
such as Reddit or financial news APIs.

Each record is individually parsed in a loop. If the timestamp format is
valid, it is converted into the standardized UTC ISO 8601 format. If the
format is invalid or unparseable, the record is discarded, and a warning
message is logged by the Log System. Once all records have been
processed, the valid, normalized timestamps are returned to the
Preprocessing Module, which then saves the updated records back to the
Data Layer.

This sequence diagram ensures that all temporal data entering the system
is clean, consistent, and compatible with time-series operations such as
alignment for correlation analysis or chart plotting thereby maintaining
high data quality and operational reliability.

The following sequence diagram (Figure 5.27) models the function
requirement (SY-FR8) which is explained in table (5.18). 

![[]{#_Toc199184383 .anchor}Figure 5.27: Trigger Visualization Updates
Sequence Diagram](media/image39.png){width="4.747684820647419in"
height="2.8774857830271214in"}

Figure 5.27 illustrates the Trigger Visualization Updates Sequence
Diagram, which models the automated mechanism for refreshing dashboard
visualizations based on new data availability supporting system-level
functional requirement SY-FR8. The sequence begins when the user opens
the dashboard UI, which then starts polling the data store at fixed
intervals. This polling is managed by the Data Store Watcher, which
checks the Data Layer for updates using the last known timestamp as a
reference.

If new data is found, the updated dataset is returned, and a refresh is
triggered. The Chart Renderer then re-renders the visual components such
as graphs and correlation tables to reflect the latest insights. If no
changes are detected, the system simply continues polling in the next
cycle without making UI modifications. In the event of a query failure
due to server unavailability or internal issues, an error is logged by
the Log System, and the dashboard continues displaying the last known
valid data to preserve continuity.

This sequence ensures that the dashboard remains responsive and current
without requiring manual refreshments. It also incorporates fault
tolerance, maintaining usability and user trust even when backend
services temporarily fail.

The following sequence diagram (Figure 5.28) models the function
requirement (SY-FR9) which is explained in table (5.19). 

![[]{#_Toc199184384 .anchor}Figure 5.28: Log Pipeline Operations
Sequence Diagram](media/image40.png){width="5.295833333333333in"
height="3.3295581802274716in"}

Figure 5.28 illustrates the Log Pipeline Operations Sequence Diagram,
which models the system\'s behavior in recording pipeline execution
events aligned with system-level functional requirement SY-FR9. This
sequence ensures that every major action in the data processing
pipeline, whether successful or failed, is logged systematically to
facilitate traceability, debugging, and monitoring.

The process begins when a user initiates the pipeline, either manually
or via a scheduled trigger. The Pipeline Controller starts execution and
logs an informational message such as \"Pipeline started\". As each task
in the pipeline is executed, a corresponding log entry is recorded. For
example, when data collection begins, the system logs \"Data collection
started\", and based on the outcome, either a success message with
record count or an error message such as \"Failed to connect to
NewsAPI\" is written to the Log System.

This logging pattern continues through subsequent stages like
preprocessing, ensuring that both major transitions and granular
outcomes are tracked. At the end of the sequence, the system logs
\"Pipeline finished\". By capturing both success and failure states
across all subsystems (collectors, preprocessors, etc.), this diagram
underscores the system's commitment to operational transparency and
facilitates efficient diagnostics and auditing in complex data
workflows.

## 

## ![A diagram of a network AI-generated content may be incorrect.](media/image41.png){width="10.17986111111111in" height="3.3125in"}5.7 Object Model Diagram

[]{#_Toc201535026 .anchor}Figure 5.29: Class Diagram

## 5.8 ER diagram 

![[]{#_Toc201535027 .anchor}Figure 5.30: ER
Diagram](media/image42.png){width="4.220833333333333in"
height="2.733406605424322in"}

The Entity-Relationship Diagram (ERD) presented in Figure 5.30
represents the logical data model for the Stock Market Sentiment
Dashboard system. It defines the structure, attributes, and
relationships of key entities involved in collecting, processing,
analysing, and storing sentiment and stock-related insights. The design
supports core features such as sentiment tracking, correlation analysis,
model evaluation, and operational job logging, ensuring data integrity
and full auditability across all components.

At the centre of the model is the **Stock** entity, which stores static
reference data for each stock being tracked, including a unique
stock_symbol and company_name. This entity is referenced by three other
entities: **SentimentRecord**, **CorrelationResult**, and **JobLog**.

- The **SentimentRecord** entity captures outputs from the sentiment
  classification process. It includes attributes such as the content
  source, sentiment score, label, the raw text, and timestamp. Each
  record is linked to the corresponding stock (stock_symbol) and the job
  that produced it (job_id), ensuring traceability.

- The **CorrelationResult** entity stores statistical outcomes of
  Pearson correlation analyses between sentiment scores and stock
  prices. It includes the date_range, computed correlation_value, and a
  timestamp (calculated_at) for when the analysis was performed. This
  entity is also tied to a specific stock via stock_symbol.

- The **ModelEvaluationResult** entity logs evaluation metrics
  (accuracy, precision, recall, f1_score) for each sentiment model used
  (such as VADER or FinBERT). It is linked to the **JobLog** via job_id,
  enabling performance tracking over time and across models.

- Finally, the **JobLog** entity provides operational transparency by
  recording the execution status (status), start_time, end_time, and any
  error or success message for each backend job. All sentiment,
  correlation, and evaluation processes are linked to a job,
  establishing a cohesive logging framework.

Overall, the ERD demonstrates a well-normalized, relational schema that
supports analytical depth, modular growth, and system auditability. It
ensures that every sentiment insight, correlation output, or model
evaluation result can be accurately traced, analysed, and reported
within the scope of the dashboard's architecture.

## 5.9 Data dictionaries

[]{#_Toc201534950 .anchor}Table 5.20: Stock Data Dictionary

  ------------------------------------------------------------------------
  **Field**       **Type**        **Description**
  --------------- --------------- ----------------------------------------
  stock_symbol    VARCHAR (10)    Primary Key. Unique ticker symbol

  Company-name    VARCHAR (100)   Full name of the company
  ------------------------------------------------------------------------

[]{#_Toc201534951 .anchor}Table 5.21: SentimentRecord Data Dictionary

  ------------------------------------------------------------------------
  **Field**       **Type**        **Description**
  --------------- --------------- ----------------------------------------
  sentiment_id    INTEGER         Primary Key. Unique ID for the sentiment
                                  record

  stock_symbol    VARCHAR (10)    Foreign Key → Stock.symbol. Ticker for
                                  related stock

  source          VARCHAR (20)    Data source

  timestamp       DATETIME        UTC-normalized timestamp when the text
                                  was posted

  score           FLOAT           Sentiment score

  label           VARCHAR(10)     Sentiment label: Positive, Neutral, or
                                  Negative

  text            TEXT            Raw or cleaned content from the source

  job_id          INTEGER         Foreign Key → JobLog.job_id. ID of the
                                  job that created this record
  ------------------------------------------------------------------------

[]{#_Toc201534952 .anchor}

Table 5.22: JobLog Data Dictionary

  ------------------------------------------------------------------------
  **Field**       **Type**        **Description**
  --------------- --------------- ----------------------------------------
  job_id          INTEGER         Primary Key. Unique job run ID

  status          VARCHAR (20)    Status of job (e.g., Completed, Failed,
                                  PartialSuccess)

  start_time      DATETIME        When the job began execution

  end_time        DATETIME        When the job ended

  message         TEXT            Logs, stack trace, or status summary
  ------------------------------------------------------------------------

[]{#_Toc201534953 .anchor}Table 5.23: CorrelationResult Data Dictionary

  ---------------------------------------------------------------------------
  **Field**           **Type**        **Description**
  ------------------- --------------- ---------------------------------------
  correlation_id      INTEGER         Primary Key. Unique ID for the
                                      correlation result

  stock_symbol        VARCHAR (10)    Foreign Key → Stock.symbol. The stock
                                      involved in the correlation

  date_range          VARCHAR(10)     Period analyzed such as (\'7d\',
                                      \'14d\')

  correlation_value   FLOAT           Pearson correlation coefficient

  calculated_at       DATETIME        When the correlation was computed
  ---------------------------------------------------------------------------

[]{#_Toc201534954 .anchor}Table 5.24: ModelEvaluationResult Data
Dictionary

  ------------------------------------------------------------------------
  **Field**       **Type**        **Description**
  --------------- --------------- ----------------------------------------
  evaluation_id   INTEGER         Primary Key. Unique evaluation record ID

  job_id          INTEGER         Foreign Key → JobLog.job_id. Job that
                                  ran the evaluation

  model_name      VARCHAR(20)     Name of the model

  accuracy        FLOAT           Accuracy metric (%)

  precision       FLOAT           Precision metric (%)

  recall          FLOAT           Recall metric (%)

  f1_score        FLOAT           F1-score metric (%)

  evaluated_at    DATETIME        When evaluation occurred
  ------------------------------------------------------------------------

# Chapter 6: Design

## 6.1 Introduction

The design phase represents a critical juncture in the software
development lifecycle, where the conceptual requirements and system
specifications are transformed into a concrete architectural blueprint
that guides the implementation process. This chapter presents a
comprehensive analysis of the design decisions and architectural
considerations undertaken for the development of the Stock Market
Sentiment Dashboard system.

The primary objective of this chapter is to demonstrate the systematic
approach employed in evaluating alternative software architectures,
justifying the selection of the most appropriate architectural pattern,
and presenting the detailed design models that form the foundation for
system implementation. The chapter encompasses an evaluation of three
candidate architectures, followed by an in-depth analysis of the
selected layered architecture, comprehensive class design modelling,
deployment strategy considerations, and lastly the Prototype of my
System Dashboard.

The design process undertaken in this project emphasizes
maintainability, scalability, and separation of concerns while ensuring
that the architectural decisions align with the functional and
non-functional requirements established in earlier phases. Through
careful analysis and comparison of architectural alternatives, this
chapter demonstrates the rationale behind key design decisions and
provides a clear roadmap for the subsequent implementation phase.

## 6.2 Overview of Software Architectures

The selection of appropriate software architecture is fundamental to the
success of any complex system development project. During the design
phase, three distinct architectural patterns were evaluated for their
suitability in addressing the project\'s specific requirements: Layered
Architecture, Microservices Architecture, and Event-Driven Architecture.
Each architectural approach offers unique advantages and presents
specific challenges that must be carefully considered in the context of
the project\'s functional requirements, scalability needs, development
constraints, and maintenance considerations.

### 6.2.1 Architecture Option 1: Event-Driven Architecture

The Event-Driven Architecture (EDA) is a software architectural pattern
where system components communicate and operate through the generation,
consumption, and reaction to events. In this model, producers emit
events when specific changes occur, and consumers or listeners react to
those events asynchronously. Middleware such as message queues or event
buses are typically used to decouple components and manage event flow.
For example, in this architecture, once the data collection module
fetches new sentiment data, it can emit an event that triggers
downstream components like the analysis engine, storage system, or
real-time dashboard updates without needing direct method calls.

**Advantages**

- **High Decoupling**: Components are loosely coupled through events,
  enabling independent development and deployment

- **Scalability**: Supports horizontal scaling as components can be
  distributed across multiple servers

- **Real-time Processing**: Enables immediate response to data changes
  and events

- **Fault Tolerance**: System continues operating even if individual
  components fail temporarily

- **Flexibility**: Easy to add new event consumers without modifying
  existing producers

**Disadvantages**

- **Increased Complexity**: Requires event brokers, message topics, and
  extensive error handling mechanisms

- **Debugging Challenges**: Asynchronous flows make execution tracing
  difficult during development

- **Infrastructure Overhead**: Demands additional middleware components
  (message queues, event buses)

- **Testing Complexity**: Unit and integration testing become more
  complicated due to indirect component invocation

- **Event Ordering Issues**: Ensuring proper event sequence can be
  challenging in distributed environments

**Evaluation of Suitability**

This architecture demonstrates **low to moderate suitability** for the
current project scope. While EDA offers excellent scalability and
real-time capabilities, the project\'s batch-processing nature and
synchronous workflow requirements make it less appropriate for this
implementation.

**Justified Rationale**

This architecture was not chosen as the primary model for the following
reasons:

- The current system operates on a scheduled, batch-processing flow,
  orchestrated via the Pipeline and Scheduler components, which are
  inherently synchronous

- No core requirement mandates asynchronous triggers or real-time event
  streaming

- The architecture would require additional infrastructure, increasing
  development and deployment complexity for a student project scope

- The project\'s primary goal is to demonstrate accurate sentiment
  analysis and insight visualization, not high-throughput event
  streaming

However, this architecture remains a valuable candidate for future
enhancements, particularly if the system evolves into a high traffic,
continuously updating production environment.

### 6.2.2 Architecture Option 2: Microservices Architecture

The Microservices Architecture decomposes the application into a
collection of loosely coupled, independently deployable services that
communicate through well-defined APIs. The system is decomposed into
specialized services including Preprocessing Service, Logging &
Monitoring Service, Sentiment Analysis Microservice, Configuration
Service, Data Collection Service, Dashboard Service, Data Storage
Service, and various supporting components. Each microservice operates
as an independent unit with its own data storage and business logic,
enabling specialized functionality and independent scaling.

**Advantages**

- **Independent Scalability**: Services can be scaled individually based
  on specific demand patterns

- **Technology Diversity**: Each service can utilize the most
  appropriate technology stack for its function

- **Fault Isolation**: Failures in one service do not cascade to others,
  improving overall system resilience

- **Team Independence**: Different teams can develop and deploy services
  independently

- **Continuous Deployment**: Supports rapid iteration and feature
  delivery through independent service updates

- **Domain Specialization**: Each service focuses on a specific business
  capability

**Disadvantages**

- **Network Complexity**: Inter-service communication introduces latency
  and potential failure points

- **Data Consistency Challenges**: Maintaining consistency across
  services requires eventual consistency patterns

- **Infrastructure Overhead**: Requires service discovery, load
  balancing, and configuration management

- **Operational Complexity**: Demands expertise in containerization,
  orchestration, and distributed monitoring

- **Testing Complexity**: Service interdependencies complicate
  integration testing

- **Distributed Monolith Risk**: Poor service boundary definition can
  lead to anti-patterns

**Evaluation of Suitability**

The Microservices Architecture offers **moderate suitability** for this
project, particularly regarding scalability and technology flexibility.
The architecture\'s benefits become most apparent in scenarios with
large development teams, complex domain boundaries, and diverse
scalability requirements.

**Justified Rationale**

While microservices offer significant advantages in large-scale,
distributed systems, they present moderate appropriateness for this
project due to complexity considerations. For a project of this scope,
the overhead of managing multiple services, inter-service communication,
and distributed system complexities may outweigh the benefits. The
architecture enables independent scaling of services based on demand,
which is beneficial for handling varying loads in financial data
processing. However, the substantial operational overhead and complexity
may not be justified for the current project requirements, though it
remains viable if future expansion plans include significant feature
diversification.

### 6.2.3 Architecture Option 3: Layered Architecture

The Layered Architecture pattern organizes system components into
horizontal layers, where each layer provides services to the layer above
it and consumes services from the layer below. The system is structured
into five distinct layers: Presentation Layer (Dashboard, Watchlist,
CorrelationCalculator, Visualizer components), Business Layer
(DataCollector, RedisCollector, FinancialCollector, NewsAPICollector
components), Service Layer (SentimentEngine component), Data Access
Layer (StorageManager, VADERModel, SentimentRecord, Stock classes), and
Infrastructure Layer (Processor, Scheduler, Pipeline, LogSystem
components).

**Advantages**

- **Clear Separation of Concerns**: Each layer has focused
  responsibilities, improving maintainability

- **Natural Workflow Mapping**: System flow aligns directly with layered
  structure (UI → Business Logic → Data)

- **Design Pattern Compatibility**: Naturally supports implemented
  patterns (Facade, Strategy, Observer, Adapter)

- **Ease of Development**: Well-understood architecture with clear
  development guidelines

- **Code Reusability**: Layer boundaries facilitate component reuse
  across different contexts

- **Academic Defensibility**: Aligns with established software
  engineering best practices

**Disadvantages**

- **Performance Overhead**: Data must pass through multiple layers,
  potentially creating bottlenecks

- **Rigid Structure**: Changes affecting multiple layers can be complex
  to implement

- **Layer Violation Temptation**: Developers may bypass layers for
  performance, breaking architectural integrity

- **Scalability Limitations**: Vertical scaling within layers may be
  constrained by the layered structure

- **Cross-cutting Concerns**: Implementing features that span multiple
  layers can be challenging

**Evaluation of Suitability**

The Layered Architecture demonstrates **high suitability** for this
project due to its natural fit with the system\'s workflow, clear
separation of concerns, and alignment with academic best practices.

**Justified Rationale**

The Layered Architecture is most appropriate for this project because it
aligns perfectly with the system\'s primary function of processing
financial data through distinct stages. The architecture supports the
natural progression from data collection (Business Layer) through
sentiment analysis processing (Service Layer) to storage and
visualization (Data Access and Presentation Layers). The clear
boundaries between layers facilitate code reusability and enable
efficient debugging and maintenance. The architecture\'s scalability
characteristics match the project\'s anticipated growth patterns,
allowing for enhancements within individual layers without affecting the
overall system structure. Furthermore, its compatibility with the
implemented design patterns and academic defensibility make it the
optimal choice.

## 6.3 Selected Software Architecture

![[]{#_Toc201535033 .anchor}Figure 6.1: Layered Architecture
Diagram](media/image43.png){width="5.891666666666667in"
height="5.108333333333333in"}

The selected software architecture for the Stock Market Sentiment
Dashboard is the **Layered Architecture**, which divides the system into
functionally distinct layers arranged in a hierarchical structure. Each
layer is responsible for a specific aspect of the system, and components
in one layer interact only with adjacent layers either above or below.
This approach ensures high cohesion within layers and low coupling
between them, making the system easier to manage, scale, and extend.

Based on the system design and class structure, the architecture is
organized into the following **five layers**:

**1. Presentation Layer**

This layer handles all user-facing functionality and visual interaction.
It includes:

- Dashboard is the main user interface displaying sentiment and price
  analysis.

- Visualizer is responsible for rendering charts such as
  sentiment-over-time and sentiment-price correlation.

- CorrelationCalculator computes analytical metrics like Pearson
  correlation.

- Watchlist manages the user's tracked stocks.

- WatchlistObserver interface for notifying UI updates based on
  watchlist changes.

This layer is reactive, interactive, and only communicates with the
Business Layer to retrieve or display processed data.

**2. Business Layer**

This is the **core orchestration layer** where all system processes are
coordinated. It includes:

- Pipeline is a **Facade** that controls the flow of the system: from
  data collection to analysis and storage.

- Scheduler triggers the pipeline at scheduled intervals.

- DataCollector handles all external data fetching and uses various
  collectors.

- Processor performs preprocessing tasks like text cleaning and
  timestamp normalization.

This layer serves as the central controller, coordinating between
integration, processing, analysis, and storage.

**3. Infrastructure Layer**

This layer supports utility functions and third-party data access. It
includes:

- Collectors: RedditCollector, FinHubCollector, NewsAPICollector, and
  MarketauxCollector, each responsible for fetching sentiment data from
  specific sources.

- APIKeyManager securely stores and validates API keys.

- RateLimitHandler handles API request limits and backoff strategies.

- LogSystem is a **Singleton** used for consistent system-wide logging.

These components support the Business Layer but do not perform core
logic themselves.

**4. Service Layer**

This layer contains the **analytical intelligence** of the system:

- SentimentEngine conducts sentiment analysis using selected models.

- SentimentModel is an interface (Strategy pattern) to abstract the use
  of different analysis models.

- VADERModel and FinBERTModel are two interchangeable sentiment
  classifiers that implement SentimentModel.

This layer focuses purely on analysing pre-processed text data and
returning meaningful sentiment scores.

**5. Data Access Layer**

This bottom-most layer handles data persistence and domain modelling. It
includes:

- StorageManager saves and retrieves sentiment records and stock data
  from persistent storage.

- SentimentRecord is the main data structure for storing sentiment
  results.

- Supporting domain models: Stock and Timestamp, which encapsulate key
  metadata.

The Data Access Layer is invoked by the Business and Service layers but
does not initiate processes itself.

Layered Architecture offers a well-balanced blend of simplicity,
modularity, and extensibility. It ensures a clean separation between
concerns while maintaining the flexibility to evolve in future versions,
such as enabling asynchronous updates or integrating additional
sentiment models. This architecture not only supports the current goals
of near-real-time data collection, analysis, and visualization but also
lays a solid foundation for potential scalability in production-grade
environments. The subsequent section, 6.4 Design Model, will further
detail the refined class structures and relationships within this chosen
architecture.

## 6.4 Design Model

![[]{#_Toc201535034 .anchor}Figure 6.2: Refined Class Diagram with
Packages and Design
Patterns](media/image44.png){width="5.897916666666666in"
height="6.011342957130359in"}

A design model serves as a detailed blueprint that captures the inner
workings of a software system. It bridges the high-level software
architecture and the actual implementation by providing a clear
representation of how individual classes, components, and services
interact. For the *Stock Market Sentiment Dashboard*, the design model
is represented through a comprehensive class diagram, which reflects
both the logical flow and layered structure of the system. The model
adheres to layered architectural principles and integrates
object-oriented design patterns to ensure maintainability, modularity,
and scalability throughout the system\'s development lifecycle.

The system is organized into **eight distinct layers**, each
encapsulating a specific set of responsibilities. These layers
collaborate in a controlled, hierarchical fashion, where upper layers
depend on the services offered by lower ones but not vice versa. This
design enforces a clean separation of concerns and facilitates easier
testing and extensibility.

At the top, the **Dashboard Layer** serves as the user-facing interface,
responsible for rendering visualizations and handling interaction. It
includes classes such as Dashboard, Visualizer, CorrelationCalculator,
and Watchlist. The Dashboard class orchestrates the user interface,
receives updates from the underlying watchlist system, and invokes
components to display sentiment trends and correlations. The Visualizer
generates sentiment-related charts, while the CorrelationCalculator
computes sentiment-price correlations using statistical techniques. The
Watchlist manages a list of stock symbols selected by the user, while
the WatchlistObserver interface enables observer-driven updates to the
dashboard when changes occur. This layer ensures a dynamic and
responsive user experience.

Beneath it lies the **Collection Layer**, which encapsulates integration
with external data sources. The DataCollector class plays a central role
by invoking specific API collectors, including RedditCollector,
FinhubCollector, NewsAPICollector, and MarketauxCollector. These
collector classes are responsible for retrieving raw sentiment data from
their respective platforms. Supporting utilities such as APIKeyManager
ensure secure API authentication, while RateLimitHandler protects the
system from exceeding external rate limits. The collection layer
isolates third-party dependencies and normalizes incoming data into a
unified format for further processing.

The **Analysis Layer** is responsible for performing sentiment
classification. At its core, the SentimentEngine delegates the
prediction task to interchangeable models through the SentimentModel
interface. The VADERModel and FinBERTModel both implement this
interface, allowing the engine to switch between models seamlessly. This
use of the Strategy design pattern enhances extensibility by enabling
additional models to be added without changing the engine\'s logic. This
layer transforms cleaned input text into structured sentiment results
with confidence scores and classifications.

Next, the **Controller Layer** handles execution logic and system
orchestration. The Pipeline class acts as the central coordinator and is
implemented as a Facade. It is responsible for executing the full data
pipeline from collection to visualization. The Scheduler component
controls periodic execution, enabling the system to run automatically at
defined intervals. This layer ensures that the system operates in a
streamlined, repeatable sequence, abstracting complex workflows behind a
simplified interface.

The **Storage Layer** is tasked with data persistence. The
StorageManager provides functionality for saving and querying sentiment
results. It manages instances of SentimentRecord, which serve as the
core data structure for storing sentiment scores, timestamps, and price
data. This layer ensures the durability of historical sentiment data and
supports future analysis.

In the **Preprocessing Layer**, the Processor handles tasks such as text
cleaning and timestamp normalization. This ensures that the raw data
collected from external APIs is sanitized and consistent before it is
analysed by the sentiment engine. The preprocessing step is critical for
maintaining the quality and integrity of downstream results.

The **Logging Layer** provides centralized logging capabilities. The
LogSystem class, implemented as a Singleton, supports uniform logging
across the system, allowing key events and errors to be recorded in a
structured, reliable manner. This design allows any component to access
the logging system without the risk of duplication or conflicting
instances.

Finally, the **Data Layer** contains the core data entities used
throughout the system. These include SentimentRecord, Stock, and
Timestamp. SentimentRecord encapsulates the outcome of sentiment
analysis, including the sentiment score and metadata such as stock
symbol and source. Stock stores information such as company name,
symbol, and price. Timestamp represents time-related data in both raw
and formatted forms. These classes act as data carriers and are used
consistently across various layers, especially by the storage, analysis,
and visualization components.

Relationships between these classes reflect a clear and logical
structure. Associations are used to define collaborations between key
components, such as between the Dashboard and its supporting classes, or
between Pipeline and the modules it invokes. Generalization
relationships express polymorphism, as seen in the implementation of
SentimentModel by VADERModel and FinBERTModel. The use of composition is
evident in classes like SentimentRecord, which embeds instances of
Timestamp and Stock to represent a complete record.

Overall, this design model accurately translates the functional and
architectural goals of the Stock Market Sentiment Dashboard into an
object-oriented blueprint. Each class adheres to the Single
Responsibility Principle, and the relationships between layers support a
clear data flow from input to insight. By incorporating design patterns
such as Strategy, Observer, Adapter, Singleton, and Facade, the model
ensures that the system remains modular, testable, and extendable. All
of which are essential qualities for both academic and real-world
software systems.

## 6.5 Deployment

Deployment in software engineering refers to the process of delivering
and running a software system within its target operational environment.
It involves distributing software components across physical or virtual
hardware nodes, ensuring all layers and services are correctly
configured to function as a cohesive application. A deployment model
helps stakeholders understand how the software operates in the real
world, highlighting resource allocations, service communication
pathways, and hardware dependencies. For the Stock Market Sentiment
Dashboard, a layered deployment strategy is used, ensuring modularity,
performance scalability, and clear separation of concerns across backend
services, frontend components, and external APIs.

### 6.5.1 Deployment Architecture Overview

The deployment of the Stock Market Sentiment Dashboard is represented in
the diagram figure 6.3, showing three main hardware environments: the
**User Device (Web Browser)**, the **Web Server**, and the **Backend
Server (Python Services)**, along with a dedicated **Database Server**.
Each node encapsulates specific logical layers and is responsible for
hosting clearly scoped software components. The communication between
these nodes is carefully mapped to reflect runtime interactions.

### 6.5.2 Component Deployment Breakdown

The **User Device** represents the frontend interface through a modern
web browser. It hosts the **Dashboard UI**, which is responsible for
rendering interactive charts and receiving real-time updates. Within
this layer, the Dashboard class and Visualizer component operate
together to visualize sentiment trends, price correlations, and
watchlist data directly in the browser.

The **Web Server** acts as the intermediary between the client and
backend services. It hosts two main containers: the **Controller Layer**
and **Presentation Services**. The Scheduler and Pipeline classes are
deployed under the controller section to manage periodic execution and
system orchestration. Under presentation services, components such as
CorrelationCalculator, Watchlist, and ChartRenderer are deployed to
support visualization logic and user preference handling via API
endpoints. These components communicate with the backend to fetch
sentiment data and trigger updates when new events occur.

The **Backend Server** houses the core business logic and system
functionality and is composed of five primary containers. The **Data
Collection Layer** contains the DataCollector, which interacts with
third-party sentiment sources through specific collector classes:
RedditCollector, FinHubCollector, NewsAPICollector, and
MarketauxCollector. Supporting utilities like APIKeyManager and
RateLimitHandler are also deployed here to ensure reliable and secure
communication with external APIs.

The **Preprocessing Layer** includes the Processor and the
TimestampNormalizer, which transform and clean the collected raw data
before analysis. The **Sentiment Analysis Engine** is responsible for
classifying sentiment. It includes the SentimentEngine, supported by
interchangeable models VADERModel and FinBERTModel, allowing for
strategic selection of NLP approaches. The **Storage Layer** includes
the StorageManager, which facilitates persistent storage operations and
interacts with the database. Lastly, the **Logging Layer** features the
LogSystem, a singleton used across all backend services to ensure
consistent logging, error tracking, and event tracing.

On a separate node, the **Database Server** hosts the **SentimentDB**.
This logical database is composed of three main tables or collections:
SentimentRecord, Timestamp, and Stock. These classes map directly to
persistent data structures that store historical sentiment results, time
metadata, and stock-specific information.

### 6.5.3 Deployment Relationships and Runtime Interaction

The **User Device** communicates with the **Web Server** over
HTTP/HTTPS, making RESTful or WebSocket-based requests to interact with
the dashboard, query watchlist data, and retrieve chart visualizations.
The **Web Server**, in turn, acts as a controller that forwards relevant
API calls to the **Backend Server**, invoking operations from the
Pipeline, Scheduler, and data processing services.

The **Backend Server** serves as the core execution engine, processing
events, orchestrating data flow, invoking external API collectors,
analysing sentiment, and persisting results. It performs most operations
asynchronously and in isolation from the frontend, promoting scalability
and decoupling between the UI and backend logic.

External APIs such as Reddit, FinHub, NewsAPI, and Marketaux are
accessed directly from the **Data Collection Layer** within the backend.
These APIs represent external services that feed the system with near
real-time or recent sentiment-related content. Proper API key validation
and rate limiting are managed internally to protect against overuse or
service denial.

All structured data output is stored within the **Database Server**, and
the StorageManager handles query optimization, filtering, and record
retrieval. This layered approach ensures a robust, secure, and scalable
deployment, where service failure or overload in one area does not
affect the functionality of others.

![[]{#_Toc201535035 .anchor}Figure 6.3 Deployment
Diagram](media/image45.png){width="9.909722222222221in"
height="4.0625in"}

## 6.6 Prototype

This extensive prototype will present a two-faced Stock Market Sentiment
Analysis structure. The user-interfaced dashboards provide users with
near-real time data on the market sentiment and their relationship with
the stocks prices and provide detailed trend analysis on an individual
stock basis and across the market. Complementing this is a robust Admin
Panel, providing system administrators with essential tools to manage
the backend data pipelines, configure APIs, monitor and check the
accuracy of sentiment analysis models, oversee storage, and maintain
overall backend system health and operations, ensuring the platform\'s
reliability and performance.

<figure>
<img src="media/image46.png" style="width:5.54583in;height:4.98185in"
alt="A screenshot of a computer AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201535028" class="anchor"></span>Figure
6.4: Dashboard Page</p></figcaption>
</figure>

The \"Stock Market Sentiment Dashboard\" provides a comprehensive, near
real-time overview of market sentiment and performance for technology
stocks. It prominently displays key summary metrics, showcases
top-performing and underperforming stocks by sentiment, provides near
real-time stock prices, and serves as the central hub for navigating to
detailed analytical sections like Stock Analysis, Correlation Insights,
and Trend Analysis.

<figure>
<img src="media/image47.png" style="width:5.9in;height:5.325in"
alt="A screenshot of a stock analysis AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201535029" class="anchor"></span>Figure
6.5: Stock Analysis Page</p></figcaption>
</figure>

The \"Stock Analysis\" interface offers a comprehensive, near-real-time
deep dive into the performance and sentiment of an individual stock. It
presents key financial data (current price, 24h change) alongside its
sentiment score and distribution. The page also provides a comparative
view of top sentiment performers and a detailed watchlist overview,
allowing users to monitor all relevant stocks in one place.

<figure>
<img src="media/image48.png" style="width:5.9in;height:4.23333in"
alt="A screenshot of a computer AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201535030" class="anchor"></span>Figure
6.6: Sentiment vs Price Page</p></figcaption>
</figure>

Sentiment vs Price Analysis interface allows comparing trend of the
sentiment directly with trend of the stock price and trading activity.
It contains a large dual-axis chart, in which it performs both sentiment
scores and stock prices on time, along with important values such as the
degree of correlation and the trend. It also gives an analysis of the
trading volume against the sentiment and gives an understanding
regarding how the two are interconnected.

<figure>
<img src="media/image49.png" style="width:5.9in;height:4.3in"
alt="A screenshot of a computer AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201535031" class="anchor"></span>Figure
6.7: Correlation Analysis Page</p></figcaption>
</figure>

The \"Correlation Analysis\" interface is dedicated to exploring the
statistical relationship between sentiment and stock price movements. It
shows major statistics such as Pearson Correlation and R-Squared,
represented in the form of scatter plots and cross-stock correlation
charts, and provides a table of correlation statistics on an individual
stock in its watchlist in detail.

<figure>
<img src="media/image50.png" style="width:5.9in;height:4.21667in"
alt="A screenshot of a computer AI-generated content may be incorrect." />
<figcaption><p><span id="_Toc201535032" class="anchor"></span>Figure
6.8: Sentiment Trends Page</p></figcaption>
</figure>

The Sentiment Trends interface provides a detailed overview of the
sentiment trends and time variations of a stock of choice. It highlights
the major trend indicators such as overall direction, volatility,
momentum and gives detailed visualizations such as a stacked area chart
of how positive, neutral and negative sentiment are distributed and a
line chart to show the overall sentiment score trend over the selected
time period.

![[]{#_Toc201802316 .anchor}Figure 6.9: Admin Dashboard
Page](media/image51.png){width="6.5in" height="2.941666666666667in"}

The central control panel is the so-called Admin Dashboard, which
provides a real-time overview of the system health, such as the state of
data pipelines, API connectivity, and storage. It also shows the latest
activities in the system and offers fast access links to other important
administrative activities that include controlling model accuracy, API
settings, and system logs.

![[]{#_Toc201802317 .anchor}Figure 6.10: Model Accuracy
Page](media/image52.png){width="6.1125in" height="2.766298118985127in"}

The Model Accuracy page will give detailed performance results of the
sentiment analysis models behind. It compares models such as VADER (on
social media data) or FinBERT (on financial news) alongside important
measures such as accuracy, precision, recall, and F1-Score to provide an
overall assessment summary on which to base model management.

![[]{#_Toc201802318 .anchor}Figure 6.11: API Configuration
Page](media/image53.png){width="6.5in" height="2.941666666666667in"}

The API Configuration interface enables the administrators to configure
and track all the external API links that are essential in data
gathering. It shows the live status of all the integrated APIs and has
input boxes to update or configure their respective API keys so that the
data flow is smooth.

![[]{#_Toc201802319 .anchor}Figure 6.12: Watchlist Manager
Page](media/image54.png){width="5.479166666666667in"
height="3.547409230096238in"}

The Watchlist Manager gives the administrators a special interface to
actively maintain the list of stocks that the system keeps track of. It
is simple to add new stock symbols, see the full list of the current
stock symbols being tracked, and delete any of them, with statistics on
how many stocks are now in the watchlist.

![[]{#_Toc201802320 .anchor}Figure 6.13: Storage Settings
Page](media/image55.png){width="6.5in" height="3.65in"}

The Storage Settings interface allows an administrator to control every
detail of data storage and maintenance. It gives a summary of the use of
storage, database status, and backup history, and it also has storage
type configuration options. It has critical data management tools to
create manual backups, export or clean data and reset the database,
which is accompanied by a breakdown of how the data is used in detail.

![[]{#_Toc201802321 .anchor}Figure 6.14: System Logs
Page](media/image56.png){width="6.5in" height="3.3916666666666666in"}

System Logs interface is an important instrument to keep track of all
the activity on the system and help in debugging. It gives a total
number of logs, errors, warnings and informational messages and also
gives a detailed list of the latest events in the system that can be
filtered, each containing timestamps, log level and descriptive
messages, to make it easier to monitor.

## 6.7 Conclusion

The design of the Stock Market Sentiment Dashboard is rooted in a
layered architectural approach that emphasizes modularity, scalability,
and maintainability. Through a clearly structured design model and
well-defined class responsibilities, the system leverages key
object-oriented principles and design patterns including Facade,
Strategy, Observer, Adapter, and Singleton to ensure clean separation of
concerns and extensibility across all layers. The selection of the
Layered Architecture was driven by its alignment with the system's data
flow and its suitability for orchestrating processes such as data
collection, preprocessing, sentiment analysis, storage, and
visualization in a controlled and logical manner.

Deployment considerations further reinforce this structured approach,
outlining a practical and scalable runtime environment across user, web,
backend, and database nodes. Together, these design decisions provide a
strong and flexible foundation for the upcoming implementation phase,
enabling efficient development, focused testing, and seamless
integration of core functionalities in the subsequent stages of the
project.

# Chapter 7: Implementation Plan

## 7.1 Introduction

This chapter outlines the implementation plan for the Project*,*
detailing the systematic process of transforming the architectural and
design models from Chapter 6 into a fully functional software solution.
While the previous chapter focused on the logical and structural
foundations of the system, this section shifts attention to the
practical execution of the project. It breaks the implementation process
into well-defined phases and actionable tasks, organized in a sequence
that reflects the system's development flow from initial coding to final
deployment and testing.

The main part of this plan is a detailed **Gantt chart**, as it
graphically illustrates the project schedule during the 14 weeks of the
academic trimester. The chart emphasizes the durations of tasks, major
milestones, interdependencies and the critical path to the successful
delivery as a whole. It is a planning and monitoring device as it
assists in guaranteeing that every aspect of the system is created in a
unified manner and on time.

The goal of this chapter is to provide a practical, realistic and
executable implementation roadmap, which is aligned with the layered
architecture, design model and deployment strategy already developed.
This roadmap will help to develop the project during the trimester, so
it is possible to track the progress in time and manage the project
successfully.

## 7.2 Implementation Plan Phases

The implementation of the *Stock Market Sentiment Dashboard* is divided
into eight structured phases and scheduled over a 14-week period. Each
phase aligns with a specific set of tasks required to transition from
design to a working system. The order of execution follows a logical
development flow, ensuring that each component is developed, tested, and
integrated in a manageable and efficient sequence. The durations and
overlaps between phases, as illustrated in the Gantt chart, provide both
structure and flexibility to accommodate dependencies and allow
incremental progress.

![[]{#_Toc201535036 .anchor}Figure 7.1 Implementation Plan Gantt
chart](media/image57.png){width="4.029166666666667in"
height="1.9861286089238845in"}

**Phase 1: Environment Setup and Tooling (Week 1)**

This initial phase focuses on preparing the development environment and
tools necessary for the project. It includes setting up the version
control system, development environment (IDE, virtual environments),
Python libraries, and dependency management tools. It also covers
project structuring, codebase initialization, and integration with
collaboration tools such as Notion or Trello for task tracking.

**Phase 2: Data Collection Module (Week 2--3)**

In this phase, the core API integration layer is developed.
Implementation includes building the DataCollector and configuring each
collector class (RedditCollector, FinhubCollector, NewsAPICollector,
MarketauxCollector). Rate limiting logic and API key management are also
handled here. Initial testing is conducted to ensure the correct
retrieval and formatting of raw sentiment data.

**Phase 3: Preprocessing Module (Week 4)**

The focus shifts to data cleaning and normalization. The Processor class
is implemented to sanitize text, remove noise, and normalize timestamps.
Auxiliary classes such as TimestampNormalizer are created. This ensures
the collected data is in a consistent format for downstream sentiment
analysis.

**Phase 4: Sentiment Engine (Week 5--6)**

This phase involves building and testing the sentiment analysis logic.
The SentimentEngine is developed with support for both VADERModel and
FinBERTModel, following the Strategy pattern. Model selection logic is
added, and the prediction output is structured into SentimentRecord
objects. Accuracy and edge case handling are also verified.

**Phase 5: Storage Layer (Week 6--7)**

The StorageManager is implemented to handle saving and querying of
sentiment records. The persistent data models (SentimentRecord, Stock,
and Timestamp) are finalized. This layer interfaces with a local or
cloud-based database and supports filtering and retrieval operations.

**Phase 6: Dashboard and UI (Week 7--9)**

This phase marks the development of the frontend dashboard. The
Dashboard, Visualizer, and CorrelationCalculator components are
implemented to display sentiment charts, correlation graphs, and
watchlist summaries. The observer pattern is integrated to enable
dynamic UI updates when the watchlist changes.

**Phase 7: Orchestration and Logging (Week 10--11)**

The system's flow orchestration is handled through the Pipeline class
and the Scheduler, which automates periodic execution. Logging
infrastructure is centralized using the LogSystem singleton. Integration
testing begins to ensure all components work together end-to-end.

**Phase 8: Testing and Deployment (Week 12--14)**

The final phase includes comprehensive testing (unit, integration, and
UI), bug fixing, and system optimization. Deployment scripts and
configurations are prepared. The complete system is deployed in a
simulated or real environment, and final evaluations and demonstrations
are prepared.

# 

# References

Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained
Language Models. arXiv preprint arXiv.
<https://arxiv.org/abs/1908.10063>

Al-Msie'deen, R., Blasi, A. H., & Alsuwaiket, M. A. (2021). Constructing
a software requirements specification and design for an electronic IT
news magazine system. <https://arxiv.org/abs/2111.01501>

AIMultiple. (2025). Sentiment analysis: Steps & challenges in 2025.
[[https://research.aimultiple.com/sentiment-analysis/]{.underline}](https://research.aimultiple.com/sentiment-analysis/)

AIMultiple. (2025). Sentiment analysis stock market: Sources &
challenges.
[[https://research.aimultiple.com/sentiment-analysis-stock-market/]{.underline}](https://research.aimultiple.com/sentiment-analysis-stock-market/)

Cristescu, M. P., Mara, D. A., Nerișanu, R. A., Culda, L. C., & Maniu,
I. (2023). Analysing the impact of financial news sentiments over stock
prices -- a wavelet correlation. Preprints. Advance online publication.
<https://www.researchgate.net/publication/375276967>

Chen, X., Xie, H., Li, Z., Zhang, H., Tao, X., & Wang, F. L. (2025).
Sentiment analysis for stock market research: A bibliometric study.
Natural Language Processing Journal, 10, 100125.
[[https://doi.org/10.1016/j.nlp.2025.100125]{.underline}](https://doi.org/10.1016/j.nlp.2025.100125)

Catheline, C. (2022). GameStop: A Short Squeeze? HEC Paris. Retrieved
from
[https://www.vernimmen.net/ftp/researchpaper2022_c_catheline_gamestop_a_short_squeeze.pdf](https://www.vernimmen.net/ftp/researchpaper2022_c_catheline_gamestop_a_short_squeeze.pdf%20)

Deng, X., Bashlovkina, V., Han, F., Baumgartner, S., & Bendersky, M.
(2023). What do LLMs know about financial markets? A case study on
Reddit market sentiment analysis. Proceedings of the ACM Web Conference
2023, 3041--3051. <https://doi.org/10.1145/3543873.3587324>

Delgadillo, J., Kinyua, J., & Mutigwe, C. (2024). FinSoSent: Advancing
financial market sentiment analysis through pretrained large language
models. Big Data and Cognitive Computing, 8(8), 87.
<https://www.mdpi.com/2504-2289/8/8/87>

Finnhub. (2025). News sentiment API.
[[https://www.finnhub.io/docs/api/news-sentiment]{.underline}](https://www.finnhub.io/docs/api/news-sentiment)

Greyling, T., & Rossouw, S. (2025, March 26). Twitter sentiment and
stock market movements: The predictive power of social media. VoxEU.
<https://cepr.org/voxeu/columns/twitter-sentiment-and-stock-market-movements-predictive-power-social-media>

Hutto, C.J., & Gilbert, E. (2014). VADER: A Parsimonious Rule-based
Model for Sentiment Analysis of Social Media Text. Eighth International
AAAI Conference on Weblogs and Social Media.
<https://doi.org/10.1609/icwsm.v8i1.14550>

Kirtac, K., & Germano, G. (2025). Large language models in finance: What
is financial sentiment? arXiv. <https://arxiv.org/abs/2503.03612>

Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of
decision under risk. Econometrica, 47(2), 263--291. [Prospect Theory: An
Analysis of Decision under
Risk](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf)

Li, Y., & Pan, Y. (2020). A novel ensemble deep learning model for stock
prediction based on stock prices and news. arXiv.
<https://arxiv.org/abs/2007.12620>

Liu, Y., Wang, J., Long, L., Li, X., Ma, R., Wu, Y., & Chen, X. (2025).
A multi-level sentiment analysis framework for financial texts. arXiv.
<https://arxiv.org/abs/2504.02429>

Moody\'s Analytics. (n.d.). The power of news sentiment in modern
financial analysis. [The power of news sentiment in modern financial
analysis](https://www.moodys.com/web/en/us/insights/digital-transformation/the-power-of-news-sentiment-in-modern-financial-analysis.html)

Mercanti, L. (2024). Sentiment analysis in stock market predictions.
Medium.
[[https://leomercanti.medium.com/sentiment-analysis-in-stock-market-predictions-aad1822785d7]{.underline}](https://leomercanti.medium.com/sentiment-analysis-in-stock-market-predictions-aad1822785d7)

National High School Journal of Science (NHSJS). (2025). Sentiment
analysis usage within stock price predictions.
[[https://nhsjs.com/2025/sentiment-analysis-usage-within-stock-price-predictions/]{.underline}](https://nhsjs.com/2025/sentiment-analysis-usage-within-stock-price-predictions/)

PythonInvest. (2020). Sentiment analysis of financial news with Python.
[[https://pythoninvest.com/long-read/sentiment-analysis-of-financial-news]{.underline}](https://pythoninvest.com/long-read/sentiment-analysis-of-financial-news)

PyQuant News. (2024). Harnessing sentiment analysis in financial
markets.
[[https://www.pyquantnews.com/free-python-resources/harnessing-sentiment-analysis-in-financial-markets]{.underline}](https://www.pyquantnews.com/free-python-resources/harnessing-sentiment-analysis-in-financial-markets)

Pfleeger, S. L., & Atlee, J. M. (2009). Software Engineering: Theory and
Practice (4th ed.). Prentice Hall.

ResearchGate. (2024). Ethical considerations in the collection and
handling of financial data in ETC.
[[https://www.researchgate.net/publication/380079001]{.underline}](https://www.researchgate.net/publication/380079001)

Reuters. (2024, March 1). Legal transparency in AI finance: Facing the
accountability dilemma in digital decision-making.
[[https://www.reuters.com/legal/transactional/legal-transparency-ai-finance-facing-accountability-dilemma-digital-decision-2024-03-01/]{.underline}](https://www.reuters.com/legal/transactional/legal-transparency-ai-finance-facing-accountability-dilemma-digital-decision-2024-03-01/)

Shahbandari, L., Moradi, E., & Manthouri, M. (2024). Stock price
prediction using multi-faceted information based on deep recurrent
neural networks. arXiv. <https://arxiv.org/abs/2411.19766>

StockGeist. (2023). Stock market API.
[[https://www.stockgeist.ai/stock-market-api/]{.underline}](https://www.stockgeist.ai/stock-market-api/)

Wiegers, K., & Beatty, J. (2013). Software Requirements (3rd ed.).
Microsoft Press.

Yun, M. K. K. (2025). Effect of exogenous market sentiment indicators in
stock price direction prediction. Applied Soft Computing.
<https://www.sciencedirect.com/science/article/abs/pii/S0957417425013181>

Zhang, B., Yang, H., Zhou, T., Babar, A., & Liu, X.-Y. (2023). Enhancing
financial sentiment analysis via retrieval augmented large language
models. arXiv. <https://arxiv.org/abs/2310.04027>

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 
