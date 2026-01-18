'use client';

import { motion } from 'framer-motion';
import { Users, Database, Shield, Server, FileSearch, Landmark } from 'lucide-react';

const features = [
  {
    icon: Users,
    title: 'Multi-Agent',
    description: '13 specialized AI agents work in parallel to solve complex tasks efficiently.',
  },
  {
    icon: Database,
    title: 'RAG Pipeline',
    description: 'Index your knowledge base for context-aware AI responses with semantic search.',
  },
  {
    icon: Shield,
    title: 'Compliance',
    description: 'PCI-DSS, RBI, DPDP built-in scanning ensures regulatory adherence.',
  },
  {
    icon: Server,
    title: 'On-Premise',
    description: 'Run entirely on your infrastructure. No data leaves your environment.',
  },
  {
    icon: FileSearch,
    title: 'Audit Trail',
    description: 'Complete traceability of all AI actions for regulators and audits.',
  },
  {
    icon: Landmark,
    title: 'FinTech Ready',
    description: 'Payment APIs, UPI, banking workflows built with industry best practices.',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export function Features() {
  return (
    <section className="py-24 bg-background" id="features">
      <div className="mx-auto max-w-container px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-h2 text-foreground mb-4">
            Everything you need for enterprise AI
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Purpose-built for regulated industries with compliance, security, and auditability at the core.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="group p-6 rounded-xl bg-card border border-border hover:border-primary/30 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-h3 text-foreground mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
