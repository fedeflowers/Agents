# Agent Graph Visualization

You can view this graph by opening the Markdown Preview in VS Code (Ctrl+Shift+V or Cmd+Shift+V) if you have Mermaid support, or by copying the code below to [Mermaid Live Editor](https://mermaid.live/).

```mermaid
graph TD;
	__start__([<p>__start__</p>]):::first
	agent(agent)
	tools(tools)
	process_output(process_output)
	__end__([<p>__end__</p>]):::last
	__start__ --> agent;
	agent -. &nbsp;end&nbsp; .-> __end__;
	agent -.-> process_output;
	agent -.-> tools;
	tools --> agent;
	process_output --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```
