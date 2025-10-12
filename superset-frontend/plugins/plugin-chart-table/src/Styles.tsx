/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { css, styled } from '@superset-ui/core';

export default styled.div`
  ${({ theme }) => css`
    table {
      width: 100%;
      min-width: auto;
      max-width: none;
      margin: 0;
    }

    th,
    td {
      min-width: 4.3em;
    }

    thead > tr > th {
      padding-right: 0;
      position: relative;
      background: ${theme.colors.grayscale.light5};
      text-align: left;
    }
    th svg {
      color: ${theme.colors.grayscale.light2};
      margin: ${theme.gridUnit / 2}px;
    }
    th.is-sorted svg {
      color: ${theme.colors.grayscale.base};
    }
    .table > tbody > tr:first-of-type > td,
    .table > tbody > tr:first-of-type > th {
      border-top: 0;
    }

    .table > tbody tr td {
      font-feature-settings: 'tnum' 1;
    }

    .dt-controls {
      padding-bottom: 0.65em;
    }
    .dt-metric {
      text-align: right;
    }
    .dt-totals {
      font-weight: ${theme.typography.weights.bold};
    }
    .dt-is-null {
      color: ${theme.colors.grayscale.light1};
    }
    td.dt-is-filter {
      cursor: pointer;
    }
    td.dt-is-filter:hover {
      background-color: ${theme.colors.secondary.light4};
    }
    td.dt-is-active-filter,
    td.dt-is-active-filter:hover {
      background-color: ${theme.colors.secondary.light3};
    }

    .dt-global-filter {
      float: right;
    }

    .dt-truncate-cell {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .dt-truncate-cell:hover {
      overflow: visible;
      white-space: normal;
      height: auto;
    }

    .dt-pagination {
      text-align: center;
      padding: ${theme.gridUnit * 3}px ${theme.gridUnit * 4}px;
      background-color: ${theme.colors.grayscale.light5};
      border-top: 1px solid ${theme.colors.grayscale.light2};
      min-height: ${theme.gridUnit * 12}px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .dt-pagination .pagination {
      display: flex;
      align-items: center;
      gap: ${theme.gridUnit}px;
    }

    .dt-pagination .pagination > li {
      display: inline-block;
    }

    .dt-pagination .pagination > li > a,
    .dt-pagination .pagination > li > span {
      color: ${theme.colors.grayscale.dark1};
      background-color: ${theme.colors.grayscale.light5};
      border: 1px solid ${theme.colors.grayscale.light2};
      padding: ${theme.gridUnit * 1.5}px ${theme.gridUnit * 2.5}px;
      margin: 0;
      border-radius: ${theme.borderRadius}px;
      font-size: ${theme.typography.sizes.s}px;
      font-weight: ${theme.typography.weights.normal};
      line-height: 1.4;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: ${theme.gridUnit * 8}px;
      min-height: ${theme.gridUnit * 8}px;
      transition: all ${theme.transitionTiming}s ease;
      cursor: pointer;
      user-select: none;
    }

    .dt-pagination .pagination > li > a:hover,
    .dt-pagination .pagination > li > a:focus {
      color: ${theme.colors.primary.dark1};
      background-color: ${theme.colors.primary.light4};
      border-color: ${theme.colors.primary.light2};
      text-decoration: none;
      outline: none;
      box-shadow: 0 0 0 2px ${theme.colors.primary.light3}60;
      transform: translateY(-1px);
    }

    .dt-pagination .pagination > li.active > a,
    .dt-pagination .pagination > li.active > span {
      color: ${theme.colors.grayscale.light5};
      background-color: ${theme.colors.primary.base};
      border-color: ${theme.colors.primary.base};
      font-weight: ${theme.typography.weights.medium};
      box-shadow: 0 2px 4px ${theme.colors.primary.base}40;
    }

    .dt-pagination .pagination > li.active > a:hover {
      color: ${theme.colors.grayscale.light5};
      background-color: ${theme.colors.primary.dark1};
      border-color: ${theme.colors.primary.dark1};
    }

    .dt-pagination .pagination > li.disabled > a,
    .dt-pagination .pagination > li.disabled > span {
      color: ${theme.colors.grayscale.light1};
      background-color: ${theme.colors.grayscale.light4};
      border-color: ${theme.colors.grayscale.light3};
      cursor: not-allowed;
      opacity: 0.6;
    }

    .dt-pagination .pagination > li.disabled > a:hover {
      color: ${theme.colors.grayscale.light1};
      background-color: ${theme.colors.grayscale.light4};
      border-color: ${theme.colors.grayscale.light3};
      box-shadow: none;
    }

    .dt-pagination .pagination > li > span.dt-pagination-ellipsis {
      background: transparent;
      border: none;
      color: ${theme.colors.grayscale.base};
      cursor: default;
      padding: ${theme.gridUnit * 1.5}px ${theme.gridUnit}px;
    }

    .dt-pagination .pagination > li > span.dt-pagination-ellipsis:hover,
    .dt-pagination .pagination > li > span.dt-pagination-ellipsis:focus {
      background: transparent;
      border: none;
      color: ${theme.colors.grayscale.base};
      box-shadow: none;
    }

    .dt-no-results {
      text-align: center;
      padding: 1em 0.6em;
    }

    .right-border-only {
      border-right: 2px solid ${theme.colors.grayscale.light2};
    }
    table .right-border-only:last-child {
      border-right: none;
    }
  `}
`;
