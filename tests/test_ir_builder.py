"""Tests for IR builder module."""

import tempfile
from pathlib import Path

import pytest

from vsi2wm.ir_builder import IRBuilder, build_ir_from_vsi


class TestIRBuilder:
    """Test IRBuilder class."""

    def test_init(self):
        """Test IRBuilder initialization."""
        vsi_file = Path("test.vsi")
        builder = IRBuilder(vsi_file)
        assert builder.vsi_file_path == vsi_file
        assert builder.ir.protocol == "HTTP"
        assert builder.ir.transactions == []
        assert builder.warnings == []

    def test_build_simple_rest(self):
        """Test building IR from simple REST VSI."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="GET#/accounts">
      <rq>
        <m>
          <method>GET</method>
          <path>/accounts</path>
          <headers>
            <header name="Content-Type">application/json</header>
          </headers>
        </m>
        <bd><![CDATA[{"query": "test"}]]></bd>
      </rq>
      <rs>
        <rp id="page_1">
          <m>
            <status>200</status>
            <latency ms="40-120">range</latency>
          </m>
          <bd><![CDATA[{"page": 1, "items": []}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            assert ir.protocol == "HTTP"
            assert len(ir.transactions) == 1

            transaction = ir.transactions[0]
            assert transaction.id == "GET#/accounts"

            request = transaction.request
            assert request.method == "GET"
            assert request.path == "/accounts"
            assert request.headers["Content-Type"] == "application/json"
            assert request.body.type == "json"
            assert request.body.content == '{"query": "test"}'

            assert len(transaction.response_variants) == 1
            variant = transaction.response_variants[0]
            assert variant.status == 200
            assert variant.body.type == "json"
            assert variant.body.content == '{"page": 1, "items": []}'
            assert variant.latency.mode == "range"
            assert variant.latency.min_ms == 40
            assert variant.latency.max_ms == 120

        finally:
            Path(f.name).unlink()

    def test_build_soap_service(self):
        """Test building IR from SOAP VSI."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="SOAP#SupplierService#getSupplier">
      <rq>
        <m>
          <method>POST</method>
          <operation>getSupplier</operation>
          <soapAction>urn:SupplierService#getSupplier</soapAction>
          <endpoint>/soa-infra/services/erp/SupplierService</endpoint>
          <headers>
            <header name="Content-Type">text/xml;charset=UTF-8</header>
          </headers>
        </m>
        <bd><![CDATA[<soapenv:Envelope>...</soapenv:Envelope>]]></bd>
      </rq>
      <rs>
        <rp id="200_ok">
          <m>
            <status>200</status>
            <latency ms="50-150">range</latency>
          </m>
          <bd><![CDATA[<soapenv:Envelope>...</soapenv:Envelope>]]></bd>
        </rp>
        <rp id="404_not_found">
          <m>
            <status>404</status>
            <latency ms="50-150">range</latency>
          </m>
          <bd><![CDATA[<soapenv:Envelope>...</soapenv:Envelope>]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            assert ir.protocol == "HTTP"
            assert len(ir.transactions) == 1

            transaction = ir.transactions[0]
            assert transaction.id == "SOAP#SupplierService#getSupplier"

            request = transaction.request
            assert request.method == "POST"
            assert request.operation == "getSupplier"
            assert request.soap_action == "urn:SupplierService#getSupplier"
            assert request.headers["Content-Type"] == "text/xml;charset=UTF-8"
            assert request.body.type == "xml"

            assert len(transaction.response_variants) == 2
            assert transaction.response_variants[0].status == 200
            assert transaction.response_variants[1].status == 404

        finally:
            Path(f.name).unlink()

    def test_build_with_query_params(self):
        """Test building IR with query parameters."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="GET#/search">
      <rq>
        <m>
          <method>GET</method>
          <path>/search</path>
          <query>
            <param name="q">*</param>
            <param name="page">*</param>
            <param name="size">*</param>
          </query>
        </m>
      </rq>
      <rs>
        <rp id="results">
          <m>
            <status>200</status>
          </m>
          <bd><![CDATA[{"results": []}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            transaction = ir.transactions[0]
            request = transaction.request
            assert request.query["q"] == "*"
            assert request.query["page"] == "*"
            assert request.query["size"] == "*"

        finally:
            Path(f.name).unlink()

    def test_build_with_selection_logic(self):
        """Test building IR with selection logic."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="POST#/payments">
      <rq>
        <m>
          <method>POST</method>
          <path>/payments</path>
        </m>
        <bd><![CDATA[{"amount": 100}]]></bd>
      </rq>
      <rs>
        <rp id="approved">
          <m>
            <status>200</status>
            <selectionWeight>0.9</selectionWeight>
          </m>
          <bd><![CDATA[{"status": "approved"}]]></bd>
        </rp>
        <rp id="declined">
          <m>
            <status>200</status>
            <selectionWeight>0.1</selectionWeight>
            <matchScript language="js"><![CDATA[
var req = JSON.parse(lisa_vse_request.getBodyAsString());
req.amount > 500;
]]></matchScript>
          </m>
          <bd><![CDATA[{"status": "declined"}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            transaction = ir.transactions[0]
            assert len(transaction.response_variants) == 2

            # Check weights
            assert transaction.response_variants[0].weight == 0.9
            assert transaction.response_variants[1].weight == 0.1

            # Check selection logic
            assert transaction.selection_logic is not None
            assert "req.amount > 500" in transaction.selection_logic

        finally:
            Path(f.name).unlink()

    def test_build_with_fixed_latency(self):
        """Test building IR with fixed latency."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="GET#/health">
      <rq>
        <m>
          <method>GET</method>
          <path>/health</path>
        </m>
      </rq>
      <rs>
        <rp id="healthy">
          <m>
            <status>200</status>
            <latency ms="100">fixed</latency>
          </m>
          <bd><![CDATA[{"status": "healthy"}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            transaction = ir.transactions[0]
            variant = transaction.response_variants[0]
            assert variant.latency.mode == "fixed"
            assert variant.latency.fixed_ms == 100
            assert variant.latency.min_ms is None
            assert variant.latency.max_ms is None

        finally:
            Path(f.name).unlink()

    def test_build_with_response_headers(self):
        """Test building IR with response headers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="GET#/download">
      <rq>
        <m>
          <method>GET</method>
          <path>/download</path>
        </m>
      </rq>
      <rs>
        <rp id="file">
          <m>
            <status>200</status>
          </m>
          <headers>
            <header name="Content-Type">application/octet-stream</header>
            <header name="Content-Disposition">attachment; filename="file.pdf"</header>
          </headers>
          <bd><![CDATA[PDF content here]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            transaction = ir.transactions[0]
            variant = transaction.response_variants[0]
            assert variant.headers["Content-Type"] == "application/octet-stream"
            assert variant.headers["Content-Disposition"] == 'attachment; filename="file.pdf"'

        finally:
            Path(f.name).unlink()

    def test_build_empty_transaction(self):
        """Test building IR with empty transaction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="empty">
      <rq>
        <m>
          <method>GET</method>
          <path>/empty</path>
        </m>
      </rq>
      <rs>
        <rp id="no_body">
          <m>
            <status>204</status>
          </m>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            transaction = ir.transactions[0]
            assert transaction.request.body is None

            variant = transaction.response_variants[0]
            assert variant.status == 204
            assert variant.body is None

        finally:
            Path(f.name).unlink()

    def test_build_multiple_transactions(self):
        """Test building IR with multiple transactions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="GET#/users">
      <rq>
        <m>
          <method>GET</method>
          <path>/users</path>
        </m>
      </rq>
      <rs>
        <rp id="list">
          <m>
            <status>200</status>
          </m>
          <bd><![CDATA[{"users": []}]]></bd>
        </rp>
      </rs>
    </t>
    <t id="POST#/users">
      <rq>
        <m>
          <method>POST</method>
          <path>/users</path>
        </m>
        <bd><![CDATA[{"name": "John"}]]></bd>
      </rq>
      <rs>
        <rp id="created">
          <m>
            <status>201</status>
          </m>
          <bd><![CDATA[{"id": 1, "name": "John"}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            builder = IRBuilder(Path(f.name))
            ir = builder.build()

            assert len(ir.transactions) == 2

            # First transaction
            assert ir.transactions[0].id == "GET#/users"
            assert ir.transactions[0].request.method == "GET"
            assert ir.transactions[0].request.path == "/users"
            assert ir.transactions[0].response_variants[0].status == 200

            # Second transaction
            assert ir.transactions[1].id == "POST#/users"
            assert ir.transactions[1].request.method == "POST"
            assert ir.transactions[1].request.path == "/users"
            assert ir.transactions[1].response_variants[0].status == 201

        finally:
            Path(f.name).unlink()


class TestBuildIRFromVSI:
    """Test build_ir_from_vsi convenience function."""

    def test_build_ir_from_vsi(self):
        """Test the convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vsi", delete=False) as f:
            f.write(
                """<?xml version="1.0"?>
<serviceImage version="1.0">
  <transactions>
    <t id="test">
      <rq>
        <m>
          <method>GET</method>
          <path>/test</path>
        </m>
      </rq>
      <rs>
        <rp id="response">
          <m>
            <status>200</status>
          </m>
          <bd><![CDATA[{"result": "success"}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>"""
            )
            f.flush()

        try:
            ir = build_ir_from_vsi(Path(f.name))

            assert ir.protocol == "HTTP"
            assert len(ir.transactions) == 1
            assert ir.transactions[0].id == "test"
            assert ir.transactions[0].request.method == "GET"
            assert ir.transactions[0].request.path == "/test"

        finally:
            Path(f.name).unlink()
