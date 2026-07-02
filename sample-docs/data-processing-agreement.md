# Data Processing Agreement

## 1. Parties and Context

This Data Processing Agreement ("DPA") is entered into between Meridian Power Holdings Ltd
("Controller") and Acme Software Services Ltd ("Processor"), effective 1 January 2025.

This DPA supplements and is incorporated into the Master Services Agreement dated
1 January 2025 between the parties ("Principal Agreement").

## 2. Nature and Purpose of Processing

The Processor processes personal data on behalf of the Controller solely for the purpose
of providing the SaaS platform and related services described in the Principal Agreement.

Categories of data subjects: Controller's employees, contractors, and authorised users.

Categories of personal data processed:
- Identity data: full name, job title, employee ID
- Contact data: email address, phone number, office location
- Access and usage logs: login timestamps, feature usage, API call records
- Authentication credentials (hashed and salted; never stored in plaintext)

Sensitive categories: None. The Processor shall immediately notify the Controller if it
inadvertently receives data falling into special categories (health, biometric, etc.)
and shall securely delete such data without processing it.

## 3. Processor Obligations

The Processor shall:

3.1 Process personal data only on documented instructions from the Controller, unless
    required to do so by applicable law (in which case the Processor shall notify the
    Controller prior to such processing, where legally permitted).

3.2 Ensure that persons authorised to process personal data have committed to
    confidentiality or are under appropriate statutory obligations.

3.3 Implement technical and organisational measures as set out in Schedule A
    (Security Standards) to ensure a level of security appropriate to the risk,
    including as appropriate:
    - Pseudonymisation and encryption of personal data at rest (AES-256) and in transit (TLS 1.3)
    - Ability to ensure ongoing confidentiality, integrity, and availability of processing systems
    - Process for regularly testing and evaluating the effectiveness of technical measures

3.4 Not engage any sub-processor without prior written authorisation from the Controller.
    A list of currently authorised sub-processors is maintained at Schedule B and updated
    with 30 days advance notice of any additions or replacements. The Controller may object
    to a new sub-processor within 14 days of notification.

3.5 Assist the Controller in responding to data subject rights requests (access, erasure,
    portability, restriction) within 5 business days of receipt.

3.6 Notify the Controller of any personal data breach without undue delay and in any case
    within 24 hours of becoming aware of the breach. Notification shall include:
    - Nature of the breach and categories of data affected
    - Approximate number of data subjects affected
    - Likely consequences and measures taken or proposed

3.7 Make available all information necessary to demonstrate compliance with this DPA and
    allow for and contribute to audits conducted by the Controller or its appointed auditors.

## 4. Sub-Processors

Authorised sub-processors as at the effective date (Schedule B):

| Sub-Processor | Purpose | Location | Standard |
|--------------|---------|----------|----------|
| AWS (Amazon) | Cloud hosting — EU region | EU (Frankfurt) | ISO 27001, SOC 2 Type II |
| Datadog | Application monitoring and logging | EU | SOC 2 Type II |
| Stripe | Payment processing | EU | PCI-DSS Level 1 |

The Controller may request a full and current list of sub-processors at any time.

## 5. International Transfers

The Processor shall not transfer personal data outside the United Kingdom or European
Economic Area without either:
- An adequacy decision in force for the destination country; or
- Execution of the UK International Data Transfer Agreement (IDTA) or EU Standard
  Contractual Clauses (SCCs) with the receiving entity.

The Controller's prior written consent is required for any transfer not covered above.

## 6. Retention and Deletion

Personal data shall be retained only for the duration of the Principal Agreement
plus any statutory retention period required by law.

Upon termination of the Principal Agreement, the Processor shall:
- Delete all personal data within 30 days unless a longer retention period is required by law
- Provide written confirmation of deletion to the Controller within 35 days
- Securely destroy all physical copies and anonymise any data retained for statistical purposes

## 7. Controller Obligations

The Controller warrants that:
- It has a lawful basis for each category of personal data processed under this DPA
- It has provided all required notices to data subjects
- Any instructions issued to the Processor comply with applicable data protection legislation

## 8. Term and Termination

This DPA comes into force on the effective date and remains in force for the duration of
the Principal Agreement. Termination of the Principal Agreement automatically terminates
this DPA, subject to Clause 6 (Retention and Deletion) obligations surviving termination.

## 9. Governing Law

This DPA is governed by the laws of England and Wales. The parties submit to the
exclusive jurisdiction of the Courts of England and Wales for any disputes arising
from or related to this DPA.
